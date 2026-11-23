"""Demonstrate stored short Surface expressions over one shared detailed body.

The Host selected the illustrative statements and physical cells. This probe
uses the existing Core geometry and explicit multilayer write policy; it does
not implement automatic semantic Formation or replace the production Surface.
"""
import argparse
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"),
               str(ROOT / "packages/nollm-access/src"), str(Path(__file__).resolve().parent)]

from coverage_cli import address, coords
from nollm_core import CoreRuntime, expand_physical_coverage
from nollm_access import EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID, FileStatementStore
from project_memory import encounter, save_statement


def run_probe(field):
    original = FileStatementStore(ROOT / "sujiben/field").get("nollm.pressure.v1")
    sources = [original.source_handle, *original.context_refs]
    lower = address(0, 1, 0)
    notes = [
        ("surface.coverage", address(-1, 0, 0), "覆盖决定材料的支撑范围。"),
        ("surface.pressure", address(-1, 1, 0), "支撑不足提高写入压力。"),
        ("surface.advisory", address(-1, 0, 1), "高压力仍允许同层写入。"),
        (original.statement_id, lower, original.content_utf8),
    ]
    for identity, cell, text in notes:
        save_statement(field, identity, text, sources, (cell.q, cell.r), None,
                       layer=cell.layer, write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
    store_reads, state_reads = [], []
    original_get, original_read_bytes = FileStatementStore.get, Path.read_bytes

    def tracked_get(store, identity):
        statement = original_get(store, identity)
        store_reads.append({"id": identity, "characters": len(statement.content_utf8),
                            "utf8_bytes": len(statement.content_utf8.encode())})
        return statement

    def tracked_read_bytes(path):
        data = original_read_bytes(path)
        if path == field / "core/current_state.json":
            state_reads.append(len(data))
        return data

    with patch.object(FileStatementStore, "get", tracked_get), patch.object(Path, "read_bytes", tracked_read_bytes):
        first = encounter(field, layers=(-1,), order=0, page_size=8,
                          steps=1, limit=20, via="vertical", beam=32)
    assert first["kind"] == "surface"
    assert {p for c in first["candidates"] for p in c["previews"]} == {n[2] for n in notes[:3]}
    assert {r["id"] for r in store_reads} == {n[0] for n in notes[:3]}
    assert all(not c["text_truncated"] for c in first["candidates"])
    walks, down = [], []
    for identity, cell, text in notes[:3]:
        expansion = expand_physical_coverage(cell, "coverage_down")
        hit = next(member for member in expansion.members if member.target == lower)
        down.append({"upper": coords(cell), "lower": coords(lower),
                     "down_hits": hit.hit_count, "down_weight_q16": hit.weight_q16})
        candidate = next(c for c in first["candidates"] if c["window"] == [0, cell.q, cell.r])
        physical = encounter(field, (candidate["id"],), cursor=first["cursor"])
        selected = next(c for c in physical["candidates"] if c["physical_cell"] == coords(cell))
        local = encounter(field, (selected["id"],), cursor=physical["cursor"])
        recalled = next(x for x in local["items"] if x["id"] == original.statement_id)
        assert recalled["text"] == original.content_utf8
        assert tuple(recalled["via"]) == ("coverage_down",)
        walks.append({"entry": coords(cell), "items": local["items"],
                      "budget_exhausted": local["budget_exhausted"]})
    with CoreRuntime(field) as core:
        bridges = list(core.bridges())
        occupied = len(core.occupied_cells())
    assert not bridges and occupied == 4
    up = [{"upper": coords(m.target), "up_hits": m.hit_count,
           "up_weight_q16": m.weight_q16} for m in expand_physical_coverage(lower, "coverage_up").members]
    return {
        "source_code_baseline": "55871fc6b6b0e21c4a4c7e2297ae67dadbab1d15",
        "purpose": "Host-authored illustrative placement using an existing detailed judgment",
        "original_id": original.statement_id, "original_sources": sources,
        "surface_scope": [-1], "notes": [
            {"id": i, "cell": coords(c), "text": t, "characters": len(t), "utf8_bytes": len(t.encode())}
            for i, c, t in notes],
        "surface_characters": sum(len(n[2]) for n in notes[:3]),
        "surface_utf8_bytes": sum(len(n[2].encode()) for n in notes[:3]),
        "detail_characters": len(original.content_utf8),
        "detail_utf8_bytes": len(original.content_utf8.encode()),
        "first_surface_statement_reads": store_reads,
        "first_surface_core_state_reads": state_reads,
        "first_page": {k: v for k, v in first.items() if k != "cursor"},
        "upper_to_shared_lower": down, "shared_lower_to_upper": up, "walks": walks,
        "occupied_cells": occupied, "bridges": bridges,
        "scope_of_evidence": [
            "Three complete short upper expressions are actually stored and read as Surface text",
            "One lower current body is shared by three actual one-hop downward coverage paths",
            "CoreRuntime still loads whole state, including the lower body; observed reads are recorded",
            "Physical layer -1 and aggregation order 0 are distinct parameters",
            "Current encounter shares Surface scope and placement scope; this probe does not fix that API",
            "Host-authored example is reachability evidence, not independent semantic retrieval evaluation",
            "Up/down shares differ; no reciprocity assumption or parent/child object table is used",
            "Surface byte limits, autonomous Formation and bounded physical I/O remain design work",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="nollm-stored-surface-") as temp:
        result = run_probe(Path(temp))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    keys = ("surface_characters", "surface_utf8_bytes", "detail_characters", "detail_utf8_bytes",
            "first_surface_statement_reads", "first_surface_core_state_reads", "upper_to_shared_lower")
    print(json.dumps({key: result[key] for key in keys}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
