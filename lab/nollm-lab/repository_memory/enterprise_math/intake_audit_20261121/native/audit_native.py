"""Independent, bounded audit of PR #7's cursor and directed cell connection behavior.

Synthetic statements have no scientific evidential status. Navigation in scale
probes uses a declared geometry-membership oracle; it is not an LLM evaluation.
"""
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from unittest.mock import patch
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "runtime/scripts/runtime"))
from coverage_cli import address
from enterprise_math import research
from nollm_access import AccessDecision, AccessRuntime, AccessSurfaceNavigator, FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime, clear_physical_coverage_cache, clear_surface_order_cache


def json_view(value):
    return json.loads(json.dumps(value))


def page_view(page):
    return {k: json_view(v) for k, v in page.items() if k not in {"cursor", "start"}}


def measured_walk(field, choices=(), order=0, width=1, cursor=None, via="local", with_cursor=True, steps=1, limit=10, render_log=None):
    renders = [] if render_log is None else render_log

    def count(name, original):
        def wrapper(self, *args, **kwargs):
            page = original(self, *args, **kwargs)
            renders.append({"kind": name, "order": page.state.order, "call_count": page.state.call_count})
            return page
        return wrapper

    started = perf_counter()
    with patch.object(AccessSurfaceNavigator, "page", count("surface", AccessSurfaceNavigator.page)), \
         patch.object(AccessSurfaceNavigator, "_physical_entry_page", count("physical", AccessSurfaceNavigator._physical_entry_page)):
        result = research.walk(field, list(choices), order, width, steps, limit, via, cursor, with_cursor)
    return result, {"renders": renders, "render_count": len(renders), "elapsed_ms": round((perf_counter()-started)*1000, 3)}


def save(field, name, text, cell=None, revises=None):
    return research.save_statement(field, name, text, ["synthetic-fixture:observed-input#L1"], cell, revises)


def select_cell(field, cell, via="local"):
    page, _ = measured_walk(field)
    while True:
        candidate = next((c for c in page["candidates"] if c.get("window") == [0, *cell]), None)
        if candidate:
            physical, _ = measured_walk(field, [candidate["id"]], cursor=page["cursor"])
            selected = next(c for c in physical["candidates"] if c["physical_cell"] == [0, *cell])
            return measured_walk(field, [selected["id"]], cursor=physical["cursor"], via=via)[0]
        assert page["has_more"]
        page, _ = measured_walk(field, ["next"], cursor=page["cursor"])


def behavior(out):
    field = ROOT / "behavior-field"
    assert not field.exists(), "use a fresh fixture directory"
    for name, text, cell in [
        ("earlier", "Earlier menu item", (-10, -2)),
        ("A.v1", "Original A\nCondition a=1", (0, 0)),
        ("neighbor", "Local neighboring evidence", (1, 0)),
        ("B.v1", "Remote B\nCondition b=1", (30, 0)),
        ("B.peer", "Independent statement in B's physical cell", (30, 0)),
        ("tail", "Later menu item", (40, 0)),
    ]:
        save(field, name, text, cell)
    evidence = {"fixture": str(field), "checks": [], "navigation": []}
    page, count = measured_walk(field)
    history = []
    evidence["navigation"].append({"action": "start", "page": page_view(page), **count})
    while page["candidates"][0]["window"] != [0, 0, 0]:
        history.append("next")
        page, count = measured_walk(field, ["next"], cursor=page["cursor"])
        replay, replay_count = measured_walk(field, history)
        assert page_view(page) == page_view(replay)
        assert count["render_count"] == 1
        evidence["navigation"].append({"action": "next", "page": page_view(page), **count, "full_replay_render_count": replay_count["render_count"]})
    chosen = page["candidates"][0]["id"]
    root_cursor = page["cursor"]
    history.append(chosen)
    physical, count = measured_walk(field, [chosen], cursor=root_cursor)
    replay, replay_count = measured_walk(field, history)
    assert page_view(physical) == page_view(replay)
    assert count["render_count"] == 2
    evidence["navigation"].append({"action": "open_physical", "page": page_view(physical), **count, "full_replay_render_count": replay_count["render_count"]})
    state_before = (field / "core/current_state.json").read_bytes()
    bindings_before = (field / "access/bindings.json").read_bytes()
    clear_surface_order_cache()
    clear_physical_coverage_cache()
    rebuilt, rebuilt_count = measured_walk(field, cursor=physical["cursor"])
    assert page_view(rebuilt) == page_view(physical)
    assert (field / "core/current_state.json").read_bytes() == state_before
    assert (field / "access/bindings.json").read_bytes() == bindings_before
    evidence["checks"].append({"name": "cache deletion preserves current physical page and canonical bytes", "passed": True, **rebuilt_count})
    selected = physical["candidates"][0]["id"]
    recalled, count = measured_walk(field, [selected], cursor=physical["cursor"])
    replay, replay_count = measured_walk(field, [*history, selected])
    assert page_view(recalled) == page_view(replay)
    assert recalled["entry"] == [0, 0, 0]
    evidence["navigation"].append({"action": "select_entry", "page": recalled, **count, "full_replay_render_count": replay_count["render_count"]})

    save(field, "A.v2", "Revised A\nCondition a=2", revises="A.v1")
    refreshed, _ = measured_walk(field, cursor=physical["cursor"])
    assert refreshed["candidates"][0]["previews"] == ["Revised A"]
    revised_recall, _ = measured_walk(field, [selected], cursor=physical["cursor"])
    assert {i["id"] for i in revised_recall["items"]} == {"A.v2", "neighbor"}
    assert research.describe(field, "A.v1")["current"] is False
    evidence["checks"].append({"name": "old physical cursor returns current revision and preserves historical version", "passed": True, "page": page_view(refreshed), "recall": revised_recall})

    # Inserting an earlier cell changes the shown page. A stale candidate must
    # not silently become another physical entry; ordinary refusal is sufficient.
    stale_page, _ = measured_walk(field)
    stale_choice = stale_page["candidates"][0]["id"]
    save(field, "inserted", "New earlier occupied cell", (-20, -2))
    changed_page, _ = measured_walk(field, cursor=stale_page["cursor"])
    assert changed_page["candidates"][0]["window"] == [0, -20, -2]
    try:
        measured_walk(field, [stale_choice], cursor=stale_page["cursor"])
    except ValueError as exc:
        stale_error = str(exc)
    else:
        raise AssertionError("old menu ID silently selected a changed menu")
    evidence["checks"].append({"name": "occupancy change reopens current page and rejects displaced menu ID", "passed": True, "page": page_view(changed_page), "old_choice_error": stale_error})

    local_before = select_cell(field, (0, 0))
    connected_before = select_cell(field, (0, 0), "connected")
    added = research.stitch(field, "A-to-B", "A.v2", "B.v1")
    linked = select_cell(field, (0, 0), "connected")
    assert {i["id"] for i in linked["items"]} == {"A.v2", "neighbor", "B.v1", "B.peer"}
    assert all(i["via"] == ("bridge",) for i in linked["items"] if i["id"].startswith("B."))
    assert select_cell(field, (0, 0)) == local_before
    reverse = select_cell(field, (30, 0), "connected")
    assert "A.v2" not in {i["id"] for i in reverse["items"]}
    save(field, "B.v2", "Revised remote B\nCondition b=2", revises="B.v1")
    revised_linked = select_cell(field, (0, 0), "connected")
    assert {i["id"] for i in revised_linked["items"]} == {"A.v2", "neighbor", "B.v2", "B.peer"}
    assert research.describe(field, "B.v1")["current"] is False
    removed = research.unstitch(field, "A-to-B")
    restored = select_cell(field, (0, 0), "connected")
    assert restored == connected_before
    assert research.describe(field, "B.v2")["current"]
    evidence["checks"].append({"name": "directed cell stitch, peer recall, revised target, and exact withdrawal", "passed": True, "added": added, "before": connected_before, "linked": linked, "reverse": reverse, "revised_linked": revised_linked, "removed": removed, "restored": restored})
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"mode": "behavior", "checks_passed": len(evidence["checks"]), "output": str(out)}, ensure_ascii=False), flush=True)


def points(count):
    radius = 1
    while 1 + 3 * radius * (radius + 1) < count:
        radius += 1
    cells = [(q, r) for q in range(-radius, radius + 1) for r in range(-radius, radius + 1)
             if max(abs(q), abs(r), abs(q+r)) <= radius]
    return sorted(cells, key=lambda qr: (max(abs(qr[0]), abs(qr[1]), abs(sum(qr))), qr))[:count]


def scale(count, out, reuse=False, target_index=0, widths=None):
    field = ROOT / f"scale-field-{count}"
    target = [0, *points(count)[target_index]]
    target_id = f"fixture-{target_index:04d}"
    if not reuse:
        assert not field.exists(), "use a fresh fixture directory or --reuse"
        with CoreRuntime(field) as core, AccessRuntime(core, FileStatementStore(field), FileHandleStore(field)) as access:
            for i, cell in enumerate(points(count)):
                name = f"fixture-{i:04d}"
                access.put_statement(MemoryStatement(name, f"Independent synthetic statement {i}\nCell {cell}; diagnostic only.", "synthetic-fixture:controlled-point-set"))
                access.apply(AccessDecision(name, name, "new", target_cell=address(0, *cell), reason_text="Independent navigation fixture."))
    result = {"count": count, "target": target, "target_id": target_id, "oracle": "Known physical cell, chosen via exact source memberships of shown Surface windows; no semantic success claim", "runs": []}
    for width in (widths if widths is not None else [None, 3] if count == 128 else [None]):
        clear_surface_order_cache()
        clear_physical_coverage_cache()
        cursor = None
        choices = []
        memberships = {}
        trial = {"width": width, "observations": [], "render_count": 0, "reached": False}
        while True:
            attempt_renders = []
            try:
                page, measured = measured_walk(field, choices, order=None, width=width, cursor=cursor, limit=5, render_log=attempt_renders)
            except (ValueError, RuntimeError) as error:
                trial["render_count"] += len(attempt_renders)
                trial["failed_attempt_renders"] = attempt_renders
                trial["error"] = str(error)
                break
            trial["render_count"] += measured["render_count"]
            trial["observations"].append({"kind": page["kind"], "order": page.get("order"), "page_size": page.get("page_size"), "surface_calls": page["surface_calls"], "pages_left": page.get("pages_left"), "render_count": measured["render_count"], "start": page.get("start"), "candidate_count": len(page.get("candidates", []))})
            if page["kind"] == "entry":
                trial["reached"] = page["entry"] == target and target_id in {i["id"] for i in page["items"]}
                trial["recall"] = page
                break
            cursor = page["cursor"]
            if page["kind"] == "physical":
                match = next((c for c in page["candidates"] if c["physical_cell"] == target), None)
            else:
                if page["order"] not in memberships:
                    matching = set()
                    with CoreRuntime(field) as core:
                        after = None
                        while True:
                            raw = core.surface_page(research.SCOPE, page["order"], after, 256)
                            matching.update((p.address.q, p.address.r) for p in raw.cells if address(*target) in p.source_cells)
                            if not raw.has_more:
                                break
                            after = raw.next_after
                    memberships[page["order"]] = matching
                matching = memberships[page["order"]]
                match = next((c for c in page["candidates"] if tuple(c["window"][1:]) in matching), None)
            if match is None and not page["has_more"]:
                trial["error"] = "oracle found no matching continuation"
                break
            choices = [match["id"] if match else "next"]
        trial["last_surface_calls"] = trial["observations"][-1]["surface_calls"]
        result["runs"].append(trial)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"mode": "scale", "count": count, "target_index": target_index, "width": width, "reached": trial["reached"], "last_surface_calls": trial["last_surface_calls"], "renders": trial["render_count"], "error": trial.get("error")}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["behavior", "scale"])
    parser.add_argument("--count", type=int)
    parser.add_argument("--reuse", action="store_true", help="reuse the previously built controlled scale fixture")
    parser.add_argument("--target-index", type=int, default=0)
    parser.add_argument("--work-dir", type=Path, help="place fresh fixture and result files here; runtime still comes from this script's directory")
    args = parser.parse_args()
    if args.work_dir is not None:
        ROOT = args.work_dir.resolve()
        ROOT.mkdir(parents=True, exist_ok=True)
    if args.mode == "behavior":
        behavior(ROOT / "behavior-results.json")
    else:
        suffix = f"-target-{args.target_index}" if args.target_index else ""
        scale(args.count, ROOT / f"scale-results-{args.count}{suffix}.json", args.reuse, args.target_index)
