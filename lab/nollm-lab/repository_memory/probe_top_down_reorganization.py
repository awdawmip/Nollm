"""Replay two Host-chosen reorganizations on fresh field copies.

This one-off research probe expects the stored L-2/L-1/L0 Nollm field with the
statement IDs and cells declared below, and one complete Surface page. It records
choices already made by a real Host: reword one upper statement in place, then
try moving the binding judgment beside the encounter explanation. The constants
are a replay fixture, not an automatic semantic classifier or placement rule.
This is neither a fresh blind reading nor a comparison of model families.

All field operations use public Core/Access and shared project-memory APIs.
Only the new --output directory is written. The original field is inventoried
before copying and checked again afterwards; old experimental output is refused.
Forward inspection follows displayed coverage_down targets, including empty
intermediate cells. The resulting paths are research output, not a runtime index.

Example, from the repository root:
    python3 -B lab/nollm-lab/repository_memory/probe_top_down_reorganization.py \
        --field sujiben/field --output /tmp/nollm-reorganization-probe
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"),
               str(ROOT / "packages/nollm-access/src"), str(Path(__file__).parent)]

from nollm_core import CoreRuntime
from nollm_access import (AccessDecision, AccessRuntime, FileHandleStore,
                          FileStatementStore, EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
from coverage_cli import address, coords
from project_memory import decide, describe, encounter


OLD_UPPER = "nollm.formed.-2.encounter.v1"
OLD_BODY = "相遇共用读写，来源固定到提交。"
NEW_UPPER = "reorganization.maintenance-consequences.v1"
NEW_BODY = "追加支持保正文，修订保历史；原文可回溯。"
ROOT_CELL = (-2, 1, 1)
BINDING_FOCUS = (-1, 1, 0)
WORKFLOW_FOCUS = (-1, 2, 0)
TARGET = "nollm.binding.v3"
ORIGIN = (0, 1, -1)
DESTINATION = (0, 3, -1)

# These source windows were actually read by the Host in the original trial.
# A replay also checks that they remain among the encountered fact's sources.
HOST_SOURCES = [
    "5ceb6f36029e3ff690d53bbc1301bc77933d7227:lab/nollm-lab/repository_memory/project_memory.py#L26-L82",
    "5ceb6f36029e3ff690d53bbc1301bc77933d7227:lab/nollm-lab/repository_memory/test_project_memory.py#L57-L96",
    "e0e0dd80039d129b7a0321e1e640ffa0c987f9eb:packages/nollm-access/src/nollm_access/handle_store.py#L64-L84",
    "e0e0dd80039d129b7a0321e1e640ffa0c987f9eb:packages/nollm-access/src/nollm_access/runtime.py#L157-L202",
]

# Explicit experimental observation settings; these do not alter field config.
OBSERVATION = dict(surface_layers=(-2,), layers=(-2, -1, 0), order=0,
                   page_size=8, steps=1, beam=16, limit=20,
                   via="downward", compact=True)


def write_json(output, name, value):
    (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")


def file_manifest(field):
    """A preservation measurement for this probe, not a runtime mechanism."""
    return {str(path.relative_to(field)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(field.rglob("*")) if path.is_file()}


def manifest_changes(before, after):
    return {"missing": sorted(before.keys() - after.keys()),
            "added": sorted(after.keys() - before.keys()),
            "changed": sorted(path for path in before.keys() & after.keys()
                              if before[path] != after[path])}


def visible_page(page):
    return {key: value for key, value in page.items() if key != "cursor"}


def visible_bytes(page):
    # Minified JSON excluding cursor; NOT pretty-printed CLI bytes or disk I/O.
    return len(json.dumps(visible_page(page), ensure_ascii=False,
                          separators=(",", ":")).encode("utf-8"))


def require_complete(page):
    if page.get("has_more") or page.get("budget_exhausted"):
        raise ValueError("This finite-fixture probe requires complete displayed pages")
    if any(candidate.get("truncated") or candidate.get("text_truncated")
           for candidate in page.get("candidates", ())):
        raise ValueError("A clipped Surface cannot establish this probe's coverage")


def one_shown(items, predicate, label):
    selected = [item for item in items if predicate(item)]
    if len(selected) != 1:
        raise ValueError(f"Expected exactly one already displayed {label}; got {len(selected)}")
    return selected[0]


def observe_host_choices(field, output, label, *, upper_id=OLD_UPPER, upper_body=OLD_BODY,
                         finish=True):
    """Replay the known Host path, selecting IDs only from actual returned pages."""
    pages = []

    def read(name, *args, **kwargs):
        page = encounter(field, *args, **kwargs)
        require_complete(page)
        pages.append({"step": name, "page": visible_page(page)})
        return page

    first = read("surface", **OBSERVATION)
    if first["kind"] != "surface":
        raise ValueError("Expected the stored upper Surface")
    selected = one_shown(first["candidates"], lambda item: upper_body in item["previews"],
                         "Host-chosen upper expression")
    physical = read("physical", (selected["id"],), cursor=first["cursor"])
    chosen = one_shown(physical["candidates"],
                      lambda item: tuple(item["physical_cell"]) == ROOT_CELL,
                      "Host-chosen physical entry")
    root = read("root", (chosen["id"],), cursor=physical["cursor"])
    one_shown(root["items"], lambda item: item["id"] == upper_id, "current upper statement")
    binding = one_shown(root["descent_candidates"],
                       lambda item: tuple(item["cell"]) == BINDING_FOCUS, "binding focus")
    detail = read("binding_detail", cursor=root["cursor"], descend=binding["id"])
    one_shown(detail["items"], lambda item: item["id"] == TARGET
              and tuple(item["cell"]) == ORIGIN, "current binding judgment at its original cell")
    original_fact = describe(field, TARGET)
    if not set(HOST_SOURCES) <= set(original_fact["sources"]):
        raise ValueError("The replay's cited evidence is not present on the encountered fact")
    returned = read("return_root", cursor=detail["cursor"], ascend=True)
    workflow = one_shown(returned["descent_candidates"],
                        lambda item: tuple(item["cell"]) == WORKFLOW_FOCUS, "workflow focus")
    local = read("workflow_detail", cursor=returned["cursor"], descend=workflow["id"])
    one_shown(local["cells"], lambda item: tuple(item["cell"]) == DESTINATION,
              "previously Host-chosen move destination")
    one_shown(local["items"], lambda item: item["id"] == "nollm.adapter.v5"
              and tuple(item["cell"]) == DESTINATION, "encounter explanation beside the destination")
    if any(record["page"].get("entry", list(ROOT_CELL)) != list(ROOT_CELL) for record in pages):
        raise ValueError("The inspection changed its original entry")
    if finish:
        pages.append({"step": "defer", "page": decide(field, local["cursor"], "defer")})
    write_json(output, label + ".json", {
        "scope": "Replay of already made Host choices; not a new semantic selection test",
        "pages": pages,
    })
    return root["cursor"], original_fact


def inventory(field):
    with CoreRuntime(field) as core:
        atoms = {handle: atom for cell in core.occupied_cells()
                 for handle, atom in core.atoms_at(cell)}
        bridges = [bridge.to_mapping() for bridge in core.bridges()]
    bindings = FileHandleStore(field).bindings_for_handles(tuple(atoms))
    current = {binding.current_statement_id: {
        "cell": coords(binding.handle.geometry_address),
        "body_sha256": hashlib.sha256(atoms[binding.handle].payload_utf8.encode()).hexdigest(),
        "body_utf8_bytes": len(atoms[binding.handle].payload_utf8.encode()),
    } for binding in bindings}
    return current, bridges


def forward_sweep(field, output, label):
    """Enumerate all displayed downward routes in this fixed three-layer scope."""
    calls, roots, observed = [], [], {}
    paths = defaultdict(list)

    def read(*args, **kwargs):
        page = encounter(field, *args, **kwargs)
        require_complete(page)
        calls.append({"kind": page["kind"], "entry": page.get("entry"), "focus": page.get("focus"),
                      "visible_minified_json_utf8_bytes": visible_bytes(page),
                      "returned_statement_ids": [item["id"] for item in page.get("items", ())],
                      "body_utf8_bytes_with_repeats": sum(len(item["text"].encode())
                                                         for item in page.get("items", ()))})
        return page

    first = read(**OBSERVATION)
    if first["kind"] != "surface":
        raise ValueError("Expected one complete stored Surface page")
    for shown in first["candidates"]:
        physical = read((shown["id"],), cursor=first["cursor"])
        for candidate in physical["candidates"]:
            if not candidate["native_atoms"]:
                continue
            local = read((candidate["id"],), cursor=physical["cursor"])
            root = local["entry"]
            roots.append({"entry": root, "preview": candidate["previews"]})
            pending, visited = [local], set()
            while pending:
                page = pending.pop()
                focus = tuple(page["focus"])
                if focus in visited:
                    continue
                visited.add(focus)
                if page["entry"] != root:
                    raise ValueError("Forward traversal changed its physical root")
                for item in page["items"]:
                    observed[item["id"]] = item["text"]
                    path = [*page["focus_path"]]
                    if item["cell"] != path[-1]:
                        path.append(item["cell"])
                    if path not in paths[item["id"]]:
                        paths[item["id"]].append(path)
                # A one-step page focused at L-1 already returns L0 bodies.
                if focus[0] >= -1:
                    continue
                for target in page["descent_candidates"]:
                    # Empty intermediate cells are not pruned by occupancy or semantics.
                    pending.append(read(cursor=page["cursor"], descend=target["id"]))

    current, bridges = inventory(field)
    if {item["cell"][0] for item in current.values()} - {-2, -1, 0}:
        raise ValueError("Input lies outside this probe's fixed L-2/L-1/L0 scope")
    details = {identity for identity, item in current.items() if item["cell"][0] == 0}
    for identity, body in observed.items():
        if hashlib.sha256(body.encode()).hexdigest() != current[identity]["body_sha256"]:
            raise ValueError("A returned body differs from its current stored atom")
    result = {
        "label": label, "roots": roots, "paths": dict(paths),
        "method": "all displayed downward targets through L0, including empty intermediate cells",
        "observed_complete_bodies": observed, "independent_current_inventory": current,
        "current_count": len(current), "detail_count": len(details),
        "reachable_detail_count": len(details & observed.keys()),
        "orphan_current_ids_under_this_scope": sorted(current.keys() - observed.keys()),
        "native_api_calls": len(calls),
        "locality_api_calls": sum(call["kind"] == "locality" for call in calls),
        "visible_minified_json_utf8_bytes_total": sum(call["visible_minified_json_utf8_bytes"] for call in calls),
        "visible_minified_json_utf8_bytes_max": max(call["visible_minified_json_utf8_bytes"] for call in calls),
        "returned_body_utf8_bytes_with_repeats": sum(call["body_utf8_bytes_with_repeats"] for call in calls),
        "unique_observed_body_utf8_bytes": sum(len(body.encode()) for body in observed.values()),
        "calls": calls, "bridges": bridges,
        "limits": "Finite-fixture structural reachability; no semantic-choice guarantee or disk-I/O measurement",
    }
    write_json(output, label + ".json", result)
    return result


def roots_for(result, identity):
    return {tuple(path[0]) for path in result["paths"].get(identity, ())}


def path_set(result, identity):
    return {tuple(tuple(cell) for cell in path) for path in result["paths"].get(identity, ())}


def run(field, output):
    if not (field / "core/current_state.json").is_file():
        raise ValueError("--field must be an existing stored field")
    if output.exists():
        raise ValueError("--output must be a new directory; prior results are never overwritten")
    if output.is_relative_to(field) or field.is_relative_to(output):
        raise ValueError("The output and original field directories must not contain each other")
    before = file_manifest(field)
    output.mkdir(parents=True)
    write_json(output, "original_manifest.json", {"source": str(field), "files": before})
    base, summary_field, moved_field = (output / name for name in
                                      ("baseline_field", "summary_only_field", "moved_candidate_field"))
    shutil.copytree(field, base)
    if file_manifest(base) != before:
        raise ValueError("The copied baseline differs from the pre-copy manifest; retry from a stable input")
    observe_host_choices(base, output, "baseline_inspection")
    baseline = forward_sweep(base, output, "baseline_sweep")

    shutil.copytree(base, summary_field)
    root_cursor, original_fact = observe_host_choices(summary_field, output, "summary_before_revision", finish=False)
    old_upper = describe(summary_field, OLD_UPPER)
    revised = decide(summary_field, root_cursor, "revision", OLD_UPPER,
                     note_id=NEW_UPPER, body=NEW_BODY, sources=HOST_SOURCES)
    summary = forward_sweep(summary_field, output, "summary_only_sweep")

    shutil.copytree(summary_field, moved_field)
    observe_host_choices(moved_field, output, "move_before_apply", upper_id=NEW_UPPER,
                         upper_body=NEW_BODY, finish=False)
    with CoreRuntime(moved_field) as core, AccessRuntime(
            core, FileStatementStore(moved_field), FileHandleStore(moved_field)) as access:
        handle = access.saved_handle(TARGET)
        moved = access.apply(AccessDecision(
            "reorganization.move-binding-near-encounter", TARGET, "move",
            target_cell=address(*DESTINATION), existing_handle=handle,
            reason_text="Host replay: place state-change consequences beside the observed encounter explanation.",
            write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID))
    candidate = forward_sweep(moved_field, output, "moved_candidate_sweep")
    old_roots, new_roots = roots_for(baseline, TARGET), roots_for(candidate, TARGET)
    detail_ids = {identity for identity, item in baseline["independent_current_inventory"].items()
                  if item["cell"][0] == 0}
    evidence = {name: digest for name, digest in before.items() if name.startswith("access/statements/")}
    preservation = {}
    for label, copy in (("baseline", base), ("summary_only", summary_field), ("moved_candidate", moved_field)):
        after = file_manifest(copy)
        preservation[label] = {
            "original_evidence_files": len(evidence),
            "changed_or_missing_original_evidence": sorted(name for name, digest in evidence.items()
                                                           if after.get(name) != digest)}
    active_changes = manifest_changes(before, file_manifest(field))
    metrics = ("current_count", "detail_count", "reachable_detail_count", "native_api_calls",
               "locality_api_calls", "visible_minified_json_utf8_bytes_total",
               "visible_minified_json_utf8_bytes_max", "returned_body_utf8_bytes_with_repeats",
               "unique_observed_body_utf8_bytes", "orphan_current_ids_under_this_scope")
    report = {
        "scope": "One-off replay of two recorded Host choices; no blind test, model-family comparison or runtime automation",
        "input_field": str(field), "original_file_count": len(before),
        "summary_revision": {
            "old_id": OLD_UPPER, "old_body": old_upper["text"], "new_id": NEW_UPPER,
            "new_body": NEW_BODY, "new_body_utf8_bytes": len(NEW_BODY.encode()), "save_result": revised,
            "all_original_detail_paths_unchanged": all(path_set(baseline, identity) == path_set(summary, identity)
                                                       for identity in detail_ids),
            "old_version_still_exactly_readable": describe(summary_field, OLD_UPPER)["text"] == old_upper["text"],
            "old_version_current_after_revision": describe(summary_field, OLD_UPPER)["current"]},
        "move_candidate": {
            "statement_id": TARGET, "from_cell": list(ORIGIN), "to_cell": coords(moved.geometry_address),
            "old_root_entries": sorted(old_roots), "new_root_entries": sorted(new_roots),
            "lost_root_entries": sorted(old_roots - new_roots), "gained_root_entries": sorted(new_roots - old_roots),
            "body_and_source_description_unchanged": original_fact == describe(moved_field, TARGET),
            "bridges_unchanged": baseline["bridges"] == candidate["bridges"],
            "orphan_current_ids_after_move": candidate["orphan_current_ids_under_this_scope"],
            "old_paths": baseline["paths"][TARGET], "new_paths": candidate["paths"][TARGET]},
        "preservation": preservation, "original_active_field_changes_at_end": active_changes,
        "baseline_copy_changes_at_end": manifest_changes(before, file_manifest(base)),
        "measurement_note": "Minified JSON excludes cursor; these bytes are not pretty-printed CLI output or disk I/O. Sweep call counts exclude the separate observation/mutation replay.",
        "sweep_metrics": {result["label"]: {key: result[key] for key in metrics}
                          for result in (baseline, summary, candidate)},
    }
    report["original_witness_reproduced"] = (
        old_roots - new_roots == {(-2, 0, 0)} and new_roots - old_roots == {(-2, 2, 1)}
        and report["summary_revision"]["all_original_detail_paths_unchanged"]
        and candidate["reachable_detail_count"] == candidate["detail_count"]
        and not candidate["orphan_current_ids_under_this_scope"])
    write_json(output, "reorganization_result.json", report)
    if any(active_changes.values()) or any(report["baseline_copy_changes_at_end"].values()) or any(
            item["changed_or_missing_original_evidence"] for item in preservation.values()):
        raise ValueError("Preservation check failed; retained output describes the difference")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True, help="existing compatible three-layer baseline field")
    parser.add_argument("--output", type=Path, required=True, help="new experiment directory; must not exist")
    args = parser.parse_args()
    try:
        result = run(args.field.resolve(), args.output.resolve())
    except (ValueError, FileNotFoundError) as error:
        parser.exit(1, f"probe failed: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
