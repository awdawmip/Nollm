"""Reproduce native cross-layer geometry at a pinned Nollm source revision.

This is a deterministic geometric fixture, not semantic navigation evaluation.
It imports unchanged Core/Access and existing Lab geometry. Every memory
workspace is temporary. Source/evidence text never determines coordinates.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext
from fractions import Fraction
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

REFERENCE_COMMIT = "bafc6de4e8213d50a5ec64754c7bc87983f853ac"
SOURCE_VERSION_NOTE = (
    "Reference input version; the probe does not verify the Git revision "
    "of the supplied --source-root directory."
)


def load_native(source: Path) -> None:
    for relative in (
        "packages/nollm-core/src",
        "packages/nollm-access/src",
        "lab/nollm-lab/geometry",
    ):
        sys.path.insert(0, str(source / relative))


def interval_json(bounds: tuple[Fraction, Fraction]) -> dict[str, str]:
    result = {}
    for name, value, rounding in (
        ("lower", bounds[0], ROUND_FLOOR),
        ("upper", bounds[1], ROUND_CEILING),
    ):
        with localcontext() as context:
            context.prec = 36
            context.rounding = rounding
            result[name] = str(Decimal(value.numerator) / Decimal(value.denominator))
    return result


def cell(layer: int, q: int, r: int):
    from nollm_core import GeometryAddress
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def cell_key(address) -> str:
    return f"L{address.layer}({address.q},{address.r})"


def coverage_probe(entry) -> dict:
    from nollm_core import expand_physical_coverage
    from certified_overlap import coverage_enclosure
    from physical_geometry import hex_vertices, intersection_area, polygon_area

    source_polygon = hex_vertices(entry.layer, entry.q, entry.r)
    source_area = polygon_area(source_polygon)
    output = {}
    for direction in ("coverage_up", "coverage_down"):
        expansion = expand_physical_coverage(entry, direction)
        oracle = coverage_enclosure(entry.layer, entry.q, entry.r, direction, bits=96)
        weights = {(m.target.q, m.target.r): m.weight_q16 for m in expansion.members}
        reverse_direction = "coverage_down" if direction == "coverage_up" else "coverage_up"
        rows = []
        for member in expansion.members:
            target = member.target
            reverse = expand_physical_coverage(target, reverse_direction)
            reverse_weight = next(
                (m.weight_q16 for m in reverse.members if m.target == entry), 0
            )
            target_polygon = hex_vertices(target.layer, target.q, target.r)
            target_area = polygon_area(target_polygon)
            overlap = intersection_area(source_polygon, target_polygon)
            bounds = oracle.shares()[(target.q, target.r)]
            decimal_share = overlap / source_area
            assert bounds[0] <= Fraction(decimal_share) <= bounds[1]
            reverse_oracle = coverage_enclosure(
                target.layer, target.q, target.r, reverse_direction, bits=96
            ).shares()[(entry.q, entry.r)]
            reciprocal_error = (
                Decimal(member.weight_q16) / 65536
                - Decimal(reverse_weight) / 65536 * target_area / source_area
            )
            rows.append({
                "target": target.to_mapping(),
                "target_key": cell_key(target),
                "hit_count": member.hit_count,
                "weight_q16": member.weight_q16,
                "weight": member.weight_q16 / 65536,
                "reverse_weight_q16": reverse_weight,
                "ideal_source_share": interval_json(bounds),
                "ideal_reverse_source_share": interval_json(reverse_oracle),
                "decimal_world_overlap_area": str(overlap),
                "decimal_source_area": str(source_area),
                "decimal_target_area": str(target_area),
                "sampled_area_reciprocity_residual_in_source_share": str(reciprocal_error),
            })
        output[direction] = {
            "members": rows,
            "sample_count": expansion.sample_count,
            "fanout": expansion.fanout,
            "q16_sum": expansion.q16_sum,
            "q16_rounding_residual": expansion.q16_rounding_residual,
            "threshold_residual_q16": expansion.threshold_residual_q16,
            "ideal_target_count": len(oracle.members),
            "ideal_candidate_count": oracle.candidate_count,
            "ideal_enclosure_bits": oracle.precision_bits,
            "ideal_total_share": interval_json((oracle.total_lower, oracle.total_upper)),
            "errors_against_ideal": {
                name: interval_json(bounds)
                for name, bounds in oracle.compare_q16(weights).items()
            },
        }
    return output


def replay_witness(registry, entry, target, kernels: tuple[str, ...], expected: int) -> dict:
    """Replay one returned kernel sequence to exhibit a concrete geometric walk.

    Core exposes kernel names, not intermediate addresses. This local diagnostic
    returns one maximum-product witness; it does not claim a unique internal walk.
    """
    frontier = [(entry, 65536, (entry,), ())]
    for kernel in kernels:
        following = []
        for current, score, addresses, weights in frontier:
            for reached, weight in registry.expand_coverage(current, kernel):
                following.append((
                    reached, score * weight // 65536,
                    (*addresses, reached), (*weights, weight),
                ))
        frontier = following
    candidates = [item for item in frontier if item[0] == target and item[1] == expected]
    assert candidates, (target, kernels, expected)
    found = min(candidates, key=lambda item: tuple(a.stable_key() for a in item[2]))
    return {
        "addresses": [a.to_mapping() for a in found[2]],
        "keys": [cell_key(a) for a in found[2]],
        "edge_weights_q16": list(found[3]),
        "score_q16": found[1],
    }


def recall_json(core, entry, result) -> dict:
    return {
        "entry_count": 1,
        "budget_exhausted": result.budget_exhausted,
        "items": [
            {
                "atom_id": item.atom.atom_id,
                "cell": item.handle.geometry_address.to_mapping(),
                "cell_key": cell_key(item.handle.geometry_address),
                "score_q16": item.score_q16,
                "path": list(item.path),
                "witness": replay_witness(
                    core.kernel_registry, entry, item.handle.geometry_address,
                    item.path, item.score_q16
                ),
            }
            for item in result.items
        ],
    }


def multi_layer_probe(entry) -> dict:
    from nollm_core import (
        CoreRecallRequest, CoreRuntime, MemoryAtom, RecallBudget,
        clear_physical_coverage_cache,
    )
    fixtures = (
        ("entry", entry),
        ("coarse-a", cell(-1, 1, 0)),
        ("coarse-b", cell(-1, 2, -1)),
        ("coarse-c", cell(-1, 2, 0)),
        ("fine-dominant", cell(1, 2, -2)),
        ("lateral-neighbor", cell(0, 3, -1)),
        ("coarse-lateral", cell(-1, 0, 0)),
        ("base-two-rings", cell(0, 3, -3)),
        ("far-control", cell(0, 30, -20)),
    )
    with TemporaryDirectory(prefix="nollm-cross-layer-") as directory:
        workspace = Path(directory)
        with CoreRuntime(workspace) as core:
            for identifier, address in fixtures:
                core.put(MemoryAtom(identifier, "Geometric probe fixture: " + identifier), address)
            request = CoreRecallRequest(
                "native-three-layer", (entry,),
                ("coverage_down", "coverage_up", "lateral"),
                RecallBudget(2, 256, 1, 1, 0, 32),
            )
            before = core.export_state_bytes()
            result = core.recall(request)
            native = recall_json(core, entry, result)
            identifiers = {item.atom.atom_id for item in result.items}
            assert identifiers == {identifier for identifier, _ in fixtures} - {"far-control"}
            assert next(i for i in result.items if i.atom.atom_id == "coarse-a").path == ("coverage_up",)
            assert next(i for i in result.items if i.atom.atom_id == "fine-dominant").path == ("coverage_down",)
            lateral_only = core.recall(CoreRecallRequest(
                "lateral-only", (entry,), ("lateral",),
                RecallBudget(1, 256, 0, 1, 0, 32),
            ))
            lateral_json = recall_json(core, entry, lateral_only)
            assert next(i for i in lateral_only.items if i.atom.atom_id == "lateral-neighbor").path == ("lateral",)
            narrow = core.recall(CoreRecallRequest(
                "beam-one", (entry,), ("coverage_down", "coverage_up"),
                RecallBudget(5, 1, 1, 0, 0, 32),
            ))
            narrow_json = recall_json(core, entry, narrow)
            assert core.export_state_bytes() == before
        clear_physical_coverage_cache()
        with CoreRuntime(workspace) as core:
            replayed = core.recall(request)
            assert replayed == result
            assert core.export_state_bytes() == before
    return {
        "seed_route": "CoreRuntime.put into an isolated geometric fixture",
        "fixtures": [{"atom_id": key, "cell": address.to_mapping()} for key, address in fixtures],
        "occupied_physical_layers": [-1, 0, 1],
        "recall_budget": asdict(request.budget),
        "native_recall": native,
        "lateral_only": lateral_json,
        "reopen_and_cold_kernel_replay_equal": True,
        "recall_preserves_canonical_state": True,
        "beam_one": {
            "budget": asdict(RecallBudget(5, 1, 1, 0, 0, 32)),
            **narrow_json,
        },
    }


def layer_zero_access_probe(entry) -> dict:
    from nollm_access import (
        AccessDecision, AccessRecallRequest, AccessRuntime, FileHandleStore,
        FileStatementStore, MemoryStatement, ActiveSemanticWritePolicyError,
    )
    from nollm_core import CoreRuntime, PhysicalFieldScope, RecallBudget

    sibling = cell(0, 3, -3)
    layer_error = None
    try:
        AccessDecision(
            "nonzero", "nonzero", "new", target_cell=cell(-1, 1, 0),
            reason_text="Check the active write contract", decided_by="fixture",
        )
    except ActiveSemanticWritePolicyError as error:
        layer_error = {"type": type(error).__name__, "field": error.field, "message": str(error)}
    assert layer_error and layer_error["field"] == "layer"

    multiple_error = None
    try:
        AccessRecallRequest(
            "multiple", (entry, sibling), (),
            ("coverage_down", "coverage_up"), RecallBudget(2, 256, 1, 0, 0, 16),
        )
    except ValueError as error:
        multiple_error = str(error)
    assert multiple_error and "exactly one physical entry" in multiple_error

    with TemporaryDirectory(prefix="nollm-layer-zero-") as directory:
        workspace = Path(directory)
        with CoreRuntime(workspace) as core:
            with AccessRuntime(core, FileStatementStore(workspace), FileHandleStore(workspace)) as access:
                for key, address in (("entry", entry), ("base-two-rings", sibling)):
                    access.capture(MemoryStatement(key, "Geometric probe fixture: " + key))
                    access.apply(AccessDecision(
                        key, key, "new", target_cell=address,
                        reason_text="Explicit geometric fixture placement", decided_by="fixture",
                    ))
                occupied = [address.to_mapping() for address in core.occupied_cells()]
                before = core.export_state_bytes()
                configurations = (
                    ("entry_only", (), RecallBudget(0, 256, 1, 0, 0, 16)),
                    ("up_only", ("coverage_up",), RecallBudget(1, 256, 1, 0, 0, 16)),
                    ("up_and_down", ("coverage_down", "coverage_up"), RecallBudget(2, 256, 1, 0, 0, 16)),
                    ("lateral_one_step", ("lateral",), RecallBudget(1, 256, 0, 1, 0, 16)),
                    ("lateral_two_steps", ("lateral",), RecallBudget(2, 256, 0, 1, 0, 16)),
                )
                recalls = {}
                for name, kernels, budget in configurations:
                    result = access.recall(AccessRecallRequest(name, (entry,), (), kernels, budget))
                    recalls[name] = {
                        "budget": asdict(budget),
                        "budget_exhausted": result.budget_exhausted,
                        "items": [
                            {
                                "statement_id": item.statement_id,
                                "evidence_utf8": item.evidence_utf8,
                                "cell_key": cell_key(item.handle.geometry_address),
                                "score_q16": item.score_q16,
                                "path": list(item.path),
                                "witness": replay_witness(
                                    core.kernel_registry, entry, item.handle.geometry_address,
                                    item.path, item.score_q16,
                                ),
                            }
                            for item in result.items
                        ],
                    }
                cross = recalls["up_and_down"]["items"]
                assert {item["statement_id"] for item in cross} == {"entry", "base-two-rings"}
                sibling_result = next(item for item in cross if item["statement_id"] == "base-two-rings")
                assert sibling_result["path"] == ["coverage_up", "coverage_down"]
                assert sibling_result["score_q16"] == 568
                assert len(recalls["lateral_one_step"]["items"]) == 1
                scope = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)
                orders = core.surface_orders(scope, 3)
                surface = [asdict(info) for info in orders]
                assert all(info.native_atom_count == 2 for info in orders)
                assert all(info.aggregate_mass_q16 == 2 * 65536 for info in orders)
                assert core.export_state_bytes() == before
                assert [address.to_mapping() for address in core.occupied_cells()] == occupied
    return {
        "seed_route": "Access.capture + Access.apply(AccessDecision), decided_by=fixture",
        "occupied_cells": occupied,
        "occupied_physical_layers": [0],
        "upper_layer_has_atoms": False,
        "recalls": recalls,
        "nonzero_layer_write_rejected": layer_error,
        "multiple_physical_entries_rejected": multiple_error,
        "surface_orders": surface,
        "surface_preserves_canonical_state_and_physical_occupancy": True,
    }


def world_polygons(entry, coverage) -> dict:
    from physical_geometry import hex_center, hex_vertices, layer_side
    highlighted = {entry}
    coarse = [cell(-1, row["target"]["q"], row["target"]["r"]) for row in coverage["coverage_up"]["members"]]
    highlighted.update(coarse)
    addresses = set(highlighted)
    for center in [entry, *coarse]:
        for dq in range(-2, 3):
            for dr in range(-2, 3):
                addresses.add(cell(center.layer, center.q + dq, center.r + dr))
    polygons = []
    for address in sorted(addresses, key=lambda item: item.stable_key()):
        vertices = hex_vertices(address.layer, address.q, address.r)
        polygons.append({
            "cell": address.to_mapping(),
            "key": cell_key(address),
            "highlighted": address in highlighted,
            "center_decimal": [str(x) for x in hex_center(address.layer, address.q, address.r)],
            "vertices_decimal": [[str(x), str(y)] for x, y in vertices],
        })
    return {
        "reference_commit": REFERENCE_COMMIT,
        "source_version_note": SOURCE_VERSION_NOTE,
        "method": "existing Lab physical_geometry.hex_vertices; 72-digit Decimal world transform",
        "coordinate_convention": "unwrapped world angle L*pi/8; pointy-top hex; side=beta^(-L)",
        "entry": entry.to_mapping(),
        "layers": [
            {"layer": layer, "side_decimal": str(layer_side(layer)), "angle_degrees": layer * 22.5}
            for layer in (-1, 0)
        ],
        "coverage_up": coverage["coverage_up"],
        "polygons": polygons,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--polygons", type=Path, required=True)
    arguments = parser.parse_args()
    for output in (arguments.output, arguments.polygons):
        if output.resolve().is_relative_to(arguments.source_root.resolve()):
            parser.error("generated evidence must be outside the source tree")
    load_native(arguments.source_root.resolve())
    entry = cell(0, 2, -1)
    coverage = coverage_probe(entry)
    result = {
        "reference_commit": REFERENCE_COMMIT,
        "source_version_note": SOURCE_VERSION_NOTE,
        "experiment_kind": "Finite geometric fixtures using unchanged native packages and existing Lab oracles",
        "semantic_navigation_quality_measured": False,
        "entry": entry.to_mapping(),
        "coverage": coverage,
        "multi_layer": multi_layer_probe(entry),
        "layer_zero_access": layer_zero_access_probe(entry),
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    arguments.polygons.parent.mkdir(parents=True, exist_ok=True)
    arguments.polygons.write_text(
        json.dumps(world_polygons(entry, coverage), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "result": str(arguments.output.resolve()),
        "polygons": str(arguments.polygons.resolve()),
        "native_items": [
            [item["atom_id"], item["cell_key"], item["score_q16"], item["path"]]
            for item in result["multi_layer"]["native_recall"]["items"]
        ],
        "layer0_cross_layer_items": result["layer_zero_access"]["recalls"]["up_and_down"]["items"],
        "beam_one": result["multi_layer"]["beam_one"],
        "surface_counts": [
            [info["grid"]["aggregation_order"], info["occupied_cell_count"], info["native_atom_count"], info["aggregate_mass_q16"]]
            for info in result["layer_zero_access"]["surface_orders"]
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
