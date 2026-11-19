"""Score sealed Surface receipts and independently recover their possible physical paths."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import json
from pathlib import Path
import sys

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY))
import directional_probe
from vertical_atlas import SOURCE_REVISION, address, coords
from nollm_core import CoreRecallRequest, CoreRuntime, Q16_ONE, RecallBudget, expand_physical_coverage

KERNELS = ("coverage_down", "coverage_up")
LIMIT = 10
BEAM = 64


@lru_cache
def footprint(source, kernel):
    expansion = expand_physical_coverage(source, kernel)
    return {member.target: member for member in expansion.members}


def name(cell):
    return ",".join(map(str, coords(cell)))


def paths_from(entry):
    """Trace the two frozen steps; the 44-file field's frontier fits within beam."""
    frontier = [([], entry, Q16_ONE)]
    paths = defaultdict(list)
    paths[entry].append(([], Q16_ONE))
    edges = {}
    widths = []
    for _ in range(2):
        following = []
        for prefix, source, score in frontier:
            for kernel in KERNELS:
                opposite = "coverage_up" if kernel == "coverage_down" else "coverage_down"
                for target, member in footprint(source, kernel).items():
                    reverse = footprint(target, opposite).get(source)
                    key = name(source) + ">" + name(target)
                    edges[key] = {
                        "kernel": kernel, "hits": member.hit_count, "q16": member.weight_q16,
                        "reverse_hits": reverse.hit_count if reverse else 0,
                        "reverse_q16": reverse.weight_q16 if reverse else 0,
                    }
                    step_path = [*prefix, key]
                    next_score = score * member.weight_q16 // Q16_ONE
                    following.append((step_path, target, next_score))
                    paths[target].append((step_path, next_score))
        width = len({target for _, target, _ in following})
        if width > BEAM:
            raise ValueError("a frontier exceeds frozen beam; unpruned reconstruction is invalid")
        widths.append(width)
        frontier = following
    return paths, edges, widths


def edge_counts(keys, edges):
    rows = [edges[k] for k in keys]
    return {
        "distinct_directed_edges": len(rows),
        "forward_one_or_two_samples": sum(e["hits"] <= 2 for e in rows),
        "reverse_one_or_two_samples": sum(0 < e["reverse_hits"] <= 2 for e in rows),
        "reverse_zero_samples": sum(e["reverse_hits"] == 0 for e in rows),
        "unequal_forward_reverse_q16": sum(e["q16"] != e["reverse_q16"] for e in rows),
    }


def signature(item):
    return (item.atom.atom_id, coords(item.handle.geometry_address), list(item.path), item.score_q16)


def native_paths(core, native):
    """Replay with fixed budget, then enlarge only the result cap for a post-hoc ceiling."""
    if native["commit"] != SOURCE_REVISION or tuple(native["kernels"]) != KERNELS:
        raise ValueError("receipt differs from the frozen source or allowed kernels")
    entry = address(*native["entry"])
    if entry.layer != 0:
        raise ValueError("expected a selected layer-zero physical entry")

    def replay(limit):
        return core.recall(CoreRecallRequest("post-hoc-audit", (entry,), KERNELS,
                                            RecallBudget(2, BEAM, 2, 0, 0, limit)))

    limited = replay(LIMIT)
    actual = [(r["id"], r["cell"], r["path"], r["score_q16"]) for r in native["items"]]
    if actual != [signature(hit) for hit in limited.items] or native["budget_exhausted"] != limited.budget_exhausted:
        raise ValueError("sealed Access receipt does not match cold Core replay")
    for raw, item in zip(native["items"], limited.items, strict=True):
        if (raw["status"] != "current" or raw["text"] != item.atom.payload_utf8
                or raw["id"] != "source@" + raw["source"]):
            raise ValueError("source receipt or text differs from replayed native atom")

    paths, edges, widths = paths_from(entry)
    per_cell, winning_edges = {}, set()
    for hit in limited.items:
        cell = hit.handle.geometry_address
        if name(cell) in per_cell:
            continue
        candidates = paths[cell]
        best_score = max(score for _, score in candidates)
        best_kernels = min(tuple(edges[key]["kernel"] for key in route)
                           for route, score in candidates if score == best_score)
        if best_score != hit.score_q16 or best_kernels != hit.path:
            raise ValueError("directed footprint expansion disagrees with Core winner")
        alternatives = [route for route, score in candidates if score == best_score
                        and tuple(edges[k]["kernel"] for k in route) == hit.path]
        for route in alternatives:
            winning_edges.update(route)
        per_cell[name(cell)] = {"score_q16": best_score, "kernels": list(hit.path),
                                "compatible_routes": alternatives}

    all_found = replay(core.placement_count())
    if [signature(x) for x in all_found.items[:LIMIT]] != actual:
        raise ValueError("post-hoc uncapped recall changed the ordered top ten")
    prefix = "source@" + SOURCE_REVISION + ":"
    if any(not item.atom.atom_id.startswith(prefix) for item in all_found.items):
        raise ValueError("unexpected corpus atom")
    reachable = [item.atom.atom_id[len(prefix):] for item in all_found.items]
    direct = sum(not hit.path for hit in limited.items)
    counts = Counter(len(hit.path) for hit in limited.items)
    return {
        "entry": coords(entry), "frontier_widths_before_visited_filter": widths,
        "ranked_native_top10": reachable[:LIMIT], "ranked_reachable_before_top10": reachable,
        "zero_step": direct, "one_step": counts[1], "two_step": counts[2],
        "winning_cells": per_cell,
        "winning_edge_values": {k: edges[k] for k in sorted(winning_edges)},
        "winning_edges": edge_counts(winning_edges, edges), "explored_edges": edge_counts(edges, edges),
        "explored_small_or_one_way_edges": {k: e for k, e in sorted(edges.items())
                                            if e["hits"] <= 2 or e["reverse_hits"] <= 2},
    }


def boundary_control():
    # The control comes from e6116ef and is independent of the question corpus.
    control = directional_probe.run(certify=True)
    return {key: control[key] for key in ("up_only", "down_only", "reopened_surface_witness")}


def score_question(diagnostic, required_sources):
    """Count each required witness once, accepting exactly its pre-frozen alternatives."""
    ranked = diagnostic["ranked_reachable_before_top10"]
    top = diagnostic["ranked_native_top10"]
    accepted = set()
    evidence = []
    for witness in required_sources:
        group = {witness["path"], *witness["alternative_paths"]}
        accepted.update(group)
        rank = next((i for i, path in enumerate(ranked, 1) if path in group), None)
        status = ("outside_two_step_support" if rank is None else
                  "below_result_cap" if rank > LIMIT else "in_native_top10")
        evidence.append({"required": witness["path"], "alternatives": sorted(group - {witness["path"]}),
                         "best_uncapped_rank": rank, "status": status})
    extra = [path for path in top if path not in accepted]
    hits = len(top) - len(extra)
    status_counts = Counter(w["status"] for w in evidence)
    return {
        "gold_groups": evidence, "relevant_returned_files": hits, "other_returned_files": extra,
        "native_precision_numerator": hits, "native_precision_denominator": len(top),
        "native_recall_numerator": status_counts["in_native_top10"], "native_recall_denominator": len(evidence),
        "reachable_below_top10": status_counts["below_result_cap"],
        "missed_outside_two_step_support": status_counts["outside_two_step_support"],
    }


def audit(field, sessions, gold_path):
    questions = {q["id"]: q for q in json.loads(gold_path.read_text())["questions"]}
    reports = {}
    global_explored_edges = {}
    global_winning_edges = {}
    relevant_path_lengths = Counter()
    with CoreRuntime(field) as core:
        if core.bridges():
            raise ValueError("the frozen physical baseline requires zero bridges")
        for folder in sorted(sessions.glob("*/config.json")):
            config = json.loads(folder.read_text())
            if config["arm"] != "surface":
                continue
            key = config["id"]
            if key in reports:
                raise ValueError(f"duplicated Surface session for {key}")
            required = questions[key]["required_sources"]
            session = folder.parent
            receipt = session / "native.json"
            if receipt.exists():
                native = json.loads(receipt.read_text())
                diagnostic = native_paths(core, native)
                scores = score_question(diagnostic, required)
                other = set(scores["other_returned_files"])
                for hit in native["items"]:
                    if hit["source"].split(":", 1)[1] not in other:
                        relevant_path_lengths[len(hit["path"])] += 1
                _, explored, _ = paths_from(address(*native["entry"]))
                global_explored_edges.update(explored)
                global_winning_edges.update(diagnostic["winning_edge_values"])
                reports[key] = {"session": session.name, "status": "physical_recall",
                                **scores, **diagnostic}
            else:
                reports[key] = {"session": session.name, "status": "no_physical_recall",
                                "gold_required": len(required), "gold_returned": 0}
    missing = questions.keys() - reports.keys()
    if missing:
        raise ValueError(f"missing Surface session configs for {sorted(missing)}")
    summary = Counter()
    for row in reports.values():
        if row["status"] != "physical_recall":
            summary["sessions_without_recall"] += 1
            summary["witnesses_in_sessions_without_recall"] += row["gold_required"]
            continue
        summary["sessions_with_recall"] += 1
        for key in ("native_precision_numerator", "native_precision_denominator",
                    "native_recall_numerator", "native_recall_denominator",
                    "missed_outside_two_step_support", "reachable_below_top10",
                    "zero_step", "one_step", "two_step"):
            summary[key] += row[key]
        for category in ("winning_edges", "explored_edges"):
            for name_, count in row[category].items():
                summary[category + "_" + name_] += count
    return {
        "semantics": "Raw physical candidates; semantic grades and token-limited displayed text are separate. "
                     "Ranks beyond 10 use an offline replay increasing only max_results. Edge aggregates are "
                     "unique directed edges per question, summed over questions. Equal-scoring intermediates "
                     "compatible with Core's returned score and kernel tuple are all retained.",
        "summary": dict(summary), "sessions": reports,
        "globally_distinct_directed_edges": {"winning": edge_counts(global_winning_edges, global_winning_edges),
                                             "explored": edge_counts(global_explored_edges, global_explored_edges)},
        "relevant_returned_files_by_best_path_length": dict(sorted(relevant_path_lengths.items())),
        "independent_frozen_boundary_control": boundary_control(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name_ in ("field", "sessions", "gold", "out"):
        parser.add_argument("--" + name_, type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.field, args.sessions, args.gold)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
