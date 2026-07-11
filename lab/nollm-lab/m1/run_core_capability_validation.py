from __future__ import annotations

import argparse
import ast
from dataclasses import fields
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from nollm_core import (
    AtomHandle,
    BridgeAddCommand,
    BridgeRemoveCommand,
    BridgeSpec,
    CoreRecallRequest,
    CoreRuntime,
    CoreTraceEvent,
    GeometryAddress,
    GeometryAnchor,
    MemoryAtom,
    MoveCommand,
    PutCommand,
    RecallBudget,
    ReplaceCommand,
    available_profile_ids,
    expand_template,
    runtime_profile,
)


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "docs" / "validation" / "CORE_CAPABILITY_VALIDATION.json"
VALIDATION_SCHEMA = "nollm_core_capability_validation_v2"
VALIDATED_PATHS = (
    "packages/nollm-core/src",
    "packages/nollm-core/tests",
    "packages/nollm-snapshot/src",
    "packages/nollm-trace/src",
    "lab/nollm-lab/geometry",
    "lab/nollm-lab/m1/run_core_capability_validation.py",
    "lab/nollm-lab/m1/run_geometry_parity.py",
)


def code_tree_digest() -> str:
    files: list[Path] = []
    for relative in VALIDATED_PATHS:
        path = ROOT / relative
        files.extend(path.rglob("*") if path.is_dir() else (path,))
    digest = sha256()
    for path in sorted(
        (path for path in files if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"),
        key=lambda value: value.relative_to(ROOT).as_posix(),
    ):
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


class MemorySink:
    def __init__(self) -> None:
        self.events: list[CoreTraceEvent] = []

    def emit(self, event: CoreTraceEvent) -> None:
        self.events.append(event)


class FailingSink:
    def emit(self, event: CoreTraceEvent) -> None:
        raise RuntimeError(event.name)


def cell(layer: int, q: int, r: int, phase: str | None = None) -> GeometryAddress:
    return GeometryAddress("eisenstein_exact_v1", "capability", layer, q, r, phase)


def request(
    request_id: str,
    entry: GeometryAddress,
    kernels: tuple[str, ...] = (),
    *,
    steps: int = 2,
    layer_delta: int = 3,
    lateral: int = 1,
    bridge_steps: int = 2,
    results: int = 16,
) -> CoreRecallRequest:
    return CoreRecallRequest(
        request_id,
        (entry,),
        kernels,
        RecallBudget(steps, 32, layer_delta, lateral, bridge_steps, results),
    )


def run_sequence(root: Path, sink: object | None) -> tuple[bytes, object, object]:
    core = CoreRuntime(root, trace_sink=sink)
    entry = cell(1, 0, 0)
    handle = core.put(MemoryAtom("trace", "one"), entry)
    core.replace(handle, "two")
    recall = core.recall(request("trace", entry, steps=0, lateral=0))
    payload = core.export_state_bytes()
    core.close()
    return payload, handle, recall


def validate(root: Path) -> dict[str, object]:
    verified: dict[str, bool] = {}
    verified["memory_atom_semantic_blind"] = [field.name for field in fields(MemoryAtom)] == ["atom_id", "payload_utf8"]
    verified["addressed_handle_contract"] = [field.name for field in fields(AtomHandle)] == ["geometry_address", "local_atom_id"]
    forbidden = ("get_by_global_id", "search_by_source", "search_by_topic", "semantic_search", "embedding_search", "find_similar")
    verified["no_global_or_semantic_lookup"] = all(not hasattr(CoreRuntime, name) for name in forbidden)

    core = CoreRuntime(root / "current")
    first = core.put(MemoryAtom("first", "one"), cell(0, -3, 5))
    second = core.put(MemoryAtom("second", "two"), cell(0, 0, 0))
    core.replace(first, "one-replaced")
    moved = core.move(second, cell(0, 2, -1))
    verified["put_replace_move_get_contains"] = core.get(first).payload_utf8 == "one-replaced" and core.contains(moved) and not core.contains(second)
    verified["cell_occupancy"] = core.placement_count() == 2 and len(core.occupied_cells()) == 2 and core.atoms_at(first.geometry_address)[0][0] == first

    bridge = BridgeSpec(
        "bridge",
        GeometryAnchor("from", (first.geometry_address,)),
        GeometryAnchor("to", (cell(0, 9, -9),)),
        1 << 15,
        "normal",
        1,
        2,
    )
    batch_atom = MemoryAtom("batch", "batch")
    batch_results = core.apply_batch((PutCommand(batch_atom, cell(0, 1, 1)), ReplaceCommand(first, "batch-replaced"), BridgeAddCommand(bridge)))
    verified["atomic_batch_and_bridge_add"] = len(batch_results) == 3 and core.bridges() == (bridge,)
    before_failed_batch = core.export_state_bytes()
    try:
        core.apply_batch((PutCommand(MemoryAtom("rolled", "rolled"), cell(0, 3, 3)), MoveCommand(AtomHandle(cell(0, 99, 99), "missing"), cell(0, 4, 4))))
    except KeyError:
        pass
    verified["failed_batch_is_atomic"] = core.export_state_bytes() == before_failed_batch
    core.apply_batch((BridgeRemoveCommand("bridge"),))
    verified["bridge_remove"] = core.bridges() == ()

    canonical = core.export_state_bytes()
    verified["canonical_disk_bytes"] = canonical == core.state_path.read_bytes()
    clone = CoreRuntime(root / "clone")
    clone.import_state_bytes(canonical)
    verified["state_export_import_clone"] = clone.export_state_bytes() == canonical
    clone.put(MemoryAtom("independent", "independent"), cell(0, 7, 7))
    verified["clone_independent"] = clone.export_state_bytes() != canonical and core.export_state_bytes() == canonical
    clone.close()
    core.close()
    reopened = CoreRuntime(root / "current")
    verified["close_reopen"] = reopened.export_state_bytes() == canonical
    reopened.close()

    geometry = CoreRuntime(root / "geometry")
    templates = geometry.kernel_registry.templates()
    verified["compiled_templates_9_of_9"] = len(templates) == 9 and len({(value.profile_id, value.direction) for value in templates}) == 9
    entry = cell(1, -4, 2, "phase:x")
    up = expand_template(entry, geometry.kernel_registry.coverage_template(entry.profile_id, "coverage_up"))[0][0]
    down = expand_template(entry, geometry.kernel_registry.coverage_template(entry.profile_id, "coverage_down"))[0][0]
    lateral_target = entry.lateral(1)[0]
    bridge_target = cell(1, 12, -8, "phase:x")
    handles = {
        name: geometry.put(MemoryAtom(name, name), target)
        for name, target in (("direct", entry), ("up", up), ("down", down), ("lateral", lateral_target), ("bridge", bridge_target))
    }
    geometry.bridge_add(BridgeSpec("recall-bridge", GeometryAnchor("from", (entry,)), GeometryAnchor("to", (bridge_target,)), 1 << 15, "normal", 1, 1))
    direct = geometry.recall(request("direct", entry, steps=0, lateral=0))
    coverage = geometry.recall(request("coverage", entry, ("coverage_down", "coverage_up"), lateral=0))
    lateral_result = geometry.recall(request("lateral", entry, ("lateral",)))
    bridge_result = geometry.recall(request("bridge", entry, ("bridge",), lateral=0))
    verified["recall_direct_hit"] = direct.items[0].handle == handles["direct"]
    verified["recall_coverage_up_down"] = {item.atom.atom_id for item in coverage.items} >= {"direct", "up", "down"}
    verified["recall_lateral_ring_one"] = any(item.handle == handles["lateral"] for item in lateral_result.items)
    verified["recall_bridge_bounded"] = any(item.handle == handles["bridge"] for item in bridge_result.items)
    verified["negative_coordinates_and_mixed_phase_order"] = entry.q < 0 and tuple(sorted((cell(0, 0, 0), cell(0, 0, 0, "p")), key=lambda value: value.stable_key())) == (cell(0, 0, 0), cell(0, 0, 0, "p"))
    repeated = geometry.recall(request("repeat", entry, ("bridge", "coverage_down", "coverage_up", "lateral")))
    repeated_again = geometry.recall(request("repeat", entry, ("bridge", "coverage_down", "coverage_up", "lateral")))
    verified["recall_deterministic_repeat"] = repeated == repeated_again
    empty = geometry.recall(request("empty", cell(0, 100, -100), steps=0, lateral=0))
    limited = geometry.recall(request("limited", entry, ("lateral",), steps=0, lateral=1, results=1))
    verified["recall_empty_cell"] = empty.items == ()
    verified["recall_budget_exhausted"] = limited.budget_exhausted and len(limited.items) <= 1
    geometry.close()

    none_result = run_sequence(root / "trace-none", None)
    memory_sink = MemorySink()
    memory_result = run_sequence(root / "trace-memory", memory_sink)
    failing_result = run_sequence(root / "trace-failing", FailingSink())
    verified["none_memory_failing_trace_parity"] = none_result == memory_result == failing_result and bool(memory_sink.events)
    state_document = json.loads(none_result[0])
    verified["trace_not_in_state_bytes"] = "events" not in state_document and "trace" not in state_document

    source_root = ROOT / "packages/nollm-core/src/nollm_core"
    exact_sources = "\n".join(path.read_text(encoding="utf-8") for path in source_root.glob("*.py"))
    verified["exact_runtime_no_float_polygon_trigonometry"] = (
        all(
            not runtime_profile(profile_id).runtime_float_allowed
            and not runtime_profile(profile_id).runtime_polygon
            for profile_id in available_profile_ids()
        )
        and "math.sin" not in exact_sources
        and "math.cos" not in exact_sources
    )
    external = set()
    for path in source_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                external.update(alias.name.split(".")[0] for alias in node.names if alias.name.split(".")[0] not in sys.stdlib_module_names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                name = node.module.split(".")[0]
                if name not in sys.stdlib_module_names:
                    external.add(name)
    verified["core_stdlib_only"] = external == set()

    return {
        "verified_capabilities": dict(sorted(verified.items())),
        "known_limitations": [
            "same-process single-writer composition only",
            "no crash-recovery protocol beyond atomic file replace",
            "no semantic placement or Evidence ownership in Core",
        ],
        "unsupported_usage": [
            "private-module imports or monkeypatching",
            "direct file tampering",
            "malicious Trace callbacks",
            "concurrent direct Store mutation outside the owning composition",
        ],
        "future_scale_work": ["cross-process coordination", "PB-scale partitioning", "long-duration performance validation"],
        "not_yet_validated": ["OpenClaw Live", "real LLM placement", "memory quality", "multi-process recovery"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--code-commit")
    args = parser.parse_args()
    with TemporaryDirectory(prefix="nollm-core-capability-") as directory:
        document = validate(Path(directory))
    if not all(document["verified_capabilities"].values()):
        failed = [name for name, value in document["verified_capabilities"].items() if not value]
        raise AssertionError(f"Core capability validation failed: {failed}")
    digest = code_tree_digest()
    if args.check:
        recorded = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if recorded.get("validation_schema") != VALIDATION_SCHEMA:
            raise AssertionError("unsupported capability validation record")
        if recorded.get("validated_code_tree_digest") != digest:
            raise AssertionError("validated code tree digest mismatch")
        commit = recorded.get("validated_code_commit")
        if type(commit) is not str:
            raise AssertionError("validated_code_commit is missing")
        subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=True)
        expected = dict(document)
        expected.update(
            validation_schema=VALIDATION_SCHEMA,
            validation_command="python lab/nollm-lab/m1/run_core_capability_validation.py --check",
            validated_code_commit=commit,
            validated_code_tree_digest=digest,
        )
        if recorded != expected:
            raise AssertionError("capability validation record does not match current results")
        print(json.dumps({"status": "passed", "validated_code_commit": commit, "validated_code_tree_digest": digest, "verified_count": len(document["verified_capabilities"])}, sort_keys=True))
        return
    commit = args.code_commit or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    subprocess.run(["git", "cat-file", "-e", commit + "^{commit}"], cwd=ROOT, check=True)
    document.update(
        validation_schema=VALIDATION_SCHEMA,
        validation_command="python lab/nollm-lab/m1/run_core_capability_validation.py --check",
        validated_code_commit=commit,
        validated_code_tree_digest=digest,
    )
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "passed", "validated_code_commit": commit, "validated_code_tree_digest": digest, "verified_count": len(document["verified_capabilities"])}, sort_keys=True))


if __name__ == "__main__":
    main()
