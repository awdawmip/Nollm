"""Count application file I/O for identical legacy and paged field copies.

The fixture, migration, copies, cursor preparation and logical equality checks
are outside the measured operations. Every measured operation opens a fresh
Core/Access runtime. Reads and writes through builtins.open/io.open are counted,
including atomic temporary files and both Access and Core recovery journals.
The totals are API payload bytes, not physical disk traffic or timings.

The synthetic remote facts are explicitly authored fixture data. Their L0 cells
occupy distinct width-64 geometric partitions, separate from the local L0 cell.
The experiment makes no claim about unrelated content sharing a touched page.
No existing field is opened; all fields live in a TemporaryDirectory.

From the repository root:
    python3 -B lab/nollm-lab/repository_memory/probe_local_storage_cost.py \
        --output /tmp/nollm-local-storage-cost.json
"""
from __future__ import annotations

import argparse
import builtins
from collections import defaultdict
from contextlib import ExitStack
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[3]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"),
               str(ROOT / "packages/nollm-access/src"), str(Path(__file__).parent)]

from nollm_access import (AccessDecision, AccessRuntime, ContentBudgetPolicy,
                          EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID, FileHandleStore,
                          FileStatementStore, LayerContentBudget, MemoryStatement)
from nollm_core import CoreRuntime
from coverage_cli import address
from local_reorganization import SCHEMA_VERSION as PLAN_SCHEMA, reorganize
from project_memory import describe, encounter, save_statement


SOURCE = "fixture:local-storage-cost-v1"
WIDTH = 64
OBSERVATION = dict(surface_layers=(-2,), layers=(-2,), order=0, page_size=8,
                   steps=0, limit=8, beam=8, via="downward", compact=True)
COUNTERS = ("open_calls", "read_calls", "write_calls", "read_bytes", "write_bytes")


def _empty_counts():
    return dict.fromkeys(COUNTERS, 0)


def _logical_path(path):
    # An atomic temporary file is a real write; normalizing its random suffix
    # only keeps diagnostic output stable, never removes the write count.
    path = re.sub(r"(^|/)\.([^/]+)\.[0-9a-f]{32}\.tmp$", r"\1\2 [temporary]", path)
    return re.sub(r"(access/binding_pages/)[^/]+/", r"\1<generation>/", path)


def _category(path):
    logical = _logical_path(path).removesuffix(" [temporary]")
    if logical == "core/current_state.json":
        return "core_current_state_or_marker"
    if logical == "core/bridges.json":
        return "core_bridges"
    if logical == "core/paged_write.pending.json":
        return "core_recovery_journal"
    if logical.startswith("core/pages/"):
        return "core_occupancy_metadata" if logical.endswith(".meta.json") else "core_page_bodies"
    if logical == "access/bindings.json":
        return "access_bindings_or_marker"
    if logical.startswith("access/binding_pages/"):
        return "access_binding_pages"
    if logical.startswith("access/statements/"):
        return "access_immutable_statements"
    if logical == "access/reorganization.pending.json":
        return "access_recovery_journal"
    if logical in {"access/content_budget.json", "access/encounter.json"}:
        return "field_configuration"
    return "other"


class _MeteredFile:
    """Delegate a Python file object, counting returned/accepted payloads."""

    def __init__(self, stream, counts):
        self._stream, self._counts = stream, counts

    def _size(self, payload):
        if isinstance(payload, str):
            return len(payload.encode(self._stream.encoding or "utf-8"))
        return len(payload)

    def _read(self, method, *args, **kwargs):
        value = getattr(self._stream, method)(*args, **kwargs)
        self._counts["read_calls"] += 1
        self._counts["read_bytes"] += self._size(value)
        return value

    def read(self, *args, **kwargs):
        return self._read("read", *args, **kwargs)

    def read1(self, *args, **kwargs):
        return self._read("read1", *args, **kwargs)

    def readline(self, *args, **kwargs):
        return self._read("readline", *args, **kwargs)

    def readlines(self, *args, **kwargs):
        lines = self._stream.readlines(*args, **kwargs)
        self._counts["read_calls"] += 1
        self._counts["read_bytes"] += sum(self._size(line) for line in lines)
        return lines

    def readinto(self, buffer):
        count = self._stream.readinto(buffer)
        self._counts["read_calls"] += 1
        self._counts["read_bytes"] += count or 0
        return count

    def write(self, payload):
        count = self._stream.write(payload)
        self._counts["write_calls"] += 1
        self._counts["write_bytes"] += self._size(payload[:count])
        return count

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def __iter__(self):
        return self

    def __next__(self):
        line = self.readline()
        if not line:
            raise StopIteration
        return line

    def __getattr__(self, name):
        return getattr(self._stream, name)

    def __enter__(self):
        self._stream.__enter__()
        return self

    def __exit__(self, *args):
        return self._stream.__exit__(*args)


class FileMeter:
    """Measure successful field-file API accesses, excluding directory metadata."""

    def __init__(self, field):
        self.field = Path(field).resolve()
        self.files = defaultdict(_empty_counts)
        self._stack = ExitStack()

    def _open(self, original, file, *args, **kwargs):
        stream = original(file, *args, **kwargs)
        if isinstance(file, int):
            # os.fdopen uses io.open; current field code uses Path.open, but
            # resolve a descriptor if a future atomic helper adopts fdopen.
            try:
                file = os.readlink(f"/proc/self/fd/{file}")
            except OSError:
                return stream
        try:
            relative = Path(file).resolve().relative_to(self.field).as_posix()
        except (TypeError, ValueError):
            return stream
        counts = self.files[relative]
        counts["open_calls"] += 1
        return _MeteredFile(stream, counts)

    def __enter__(self):
        native_open, native_io_open = builtins.open, io.open
        self._stack.enter_context(patch.object(builtins, "open", lambda *a, **k: self._open(native_open, *a, **k)))
        self._stack.enter_context(patch.object(io, "open", lambda *a, **k: self._open(native_io_open, *a, **k)))
        return self

    def __exit__(self, *args):
        return self._stack.__exit__(*args)

    def summary(self, include_files=False):
        def summarize(values):
            values = tuple(values)
            return {**{key: sum(item[key] for item in values) for key in COUNTERS},
                    "opened_files": len(values),
                    "read_files": sum(item["read_calls"] > 0 for item in values),
                    "written_files": sum(item["write_calls"] > 0 for item in values)}

        groups = defaultdict(list)
        for path, counts in self.files.items():
            groups[_category(path)].append(counts)
        result = {**summarize(self.files.values()),
                  "categories": {key: summarize(values) for key, values in sorted(groups.items())}}
        if include_files:
            normalized = defaultdict(list)
            for path, counts in self.files.items():
                normalized[_logical_path(path)].append(counts)
            result["files"] = {key: summarize(values) for key, values in sorted(normalized.items())}
        return result


def _check_meter(root):
    """Check byte accounting once on controlled UTF-8 and binary API calls."""
    root.mkdir()
    (root / "read.txt").write_bytes("表\n".encode("utf-8"))
    with FileMeter(root) as meter:
        assert (root / "read.txt").read_text(encoding="utf-8") == "表\n"
        with builtins.open(root / "binary.bin", "wb") as stream:
            stream.write(b"123")
        (root / "text.txt").write_text("层", encoding="utf-8")
    result = meter.summary()
    assert result["read_bytes"] == 4 and result["write_bytes"] == 6, result
    assert result["read_files"] == 1 and result["written_files"] == 2, result


def _seed(field, remote_count, body_bytes):
    rows = [("surface.v1", "原文按层展开。", address(-2, 0, 0)),
            ("middle.v1", "中层保存条件。", address(-1, 0, 0)),
            ("detail.v1", "这里是未修改的本地正文。", address(0, 0, 0))]
    remote_cells = [address(0, WIDTH * (16 + index), WIDTH * 16) for index in range(remote_count)]
    local_partition = address(0, 0, 0).partition_id(WIDTH)
    assert local_partition not in {cell.partition_id(WIDTH) for cell in remote_cells}
    assert len({cell.partition_id(WIDTH) for cell in remote_cells}) == remote_count
    for index, cell in enumerate(remote_cells):
        prefix = f"remote fixture {index}: "
        rows.append((f"remote.{index:06d}", prefix + "x" * (body_bytes - len(prefix)), cell))
    statements = tuple(MemoryStatement(identity, body, SOURCE) for identity, body, _ in rows)
    decisions = tuple(AccessDecision(identity, identity, "new", target_cell=cell,
                                    reason_text="Explicit local-cost fixture placement.",
                                    write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
                      for identity, _, cell in rows)
    with CoreRuntime(field) as core, AccessRuntime(core, FileStatementStore(field), FileHandleStore(field)) as access:
        access.reorganize(decisions, statements=statements)
    # Only the small Surface layer has a whole-layer budget. Deep inventory is
    # deliberately outside that configured budget, not silently omitted by it.
    ContentBudgetPolicy({-2: LayerContentBudget(max_cell_atoms=4, max_cell_utf8_bytes=256,
                                              max_layer_cells=1, max_layer_utf8_bytes=256)}).save(field)
    return {"local_facts": 3, "remote_facts": remote_count,
            "remote_body_bytes_each": body_bytes, "remote_body_bytes_total": remote_count * body_bytes,
            "remote_layer": 0, "surface_layer": -2, "remote_distinct_partitions": remote_count,
            "partition_width": WIDTH, "bridges": 0}


def _logical_state(field):
    with CoreRuntime(field) as core:
        return core.export_state_bytes(), FileHandleStore(field).state_bytes()


def _cursor(field):
    page = encounter(field, prepare_write=True, **OBSERVATION)
    while page["kind"] != "locality":
        candidate, = page["candidates"]
        page = encounter(field, [candidate["id"]], cursor=page["cursor"])
    assert page["entry"] == [-2, 0, 0]
    assert {item["id"] for item in page["items"]} == {"surface.v1"}
    return page["cursor"]


def _run_operation(field, operation, include_files):
    cursor = _cursor(field) if operation == "revision_observed" else None
    with FileMeter(field) as meter:
        if operation == "surface_first_page":
            result = encounter(field, **OBSERVATION)
        elif operation == "new_at_known_cell":
            result = save_statement(field, "surface.new", "另一条短判断。", [SOURCE], (0, 0), None,
                                    layer=-2, write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
        elif operation == "revision_observed":
            result = reorganize(field, cursor, {"schema_version": PLAN_SCHEMA, "changes": [{
                "action": "revise", "target": "surface.v1", "id": "surface.v2",
                "text": "原文可在后续逐层读取。", "sources": [SOURCE]}]})
        elif operation == "revision_by_statement_id":
            result = save_statement(field, "surface.v2", "原文可在后续逐层读取。", [SOURCE], None, "surface.v1",
                                    write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
        else:
            raise ValueError(f"unknown measured operation: {operation}")
    # Correctness and final equality checks are outside the meter.
    if operation == "surface_first_page":
        assert len(result["candidates"]) == 1
        result.pop("cursor", None)
    elif operation == "revision_observed":
        assert result["commit_state"] == "committed"
        assert result["readback"][0]["id"] == "surface.v2"
    if operation != "surface_first_page":
        identity = "surface.new" if operation == "new_at_known_cell" else "surface.v2"
        assert describe(field, identity)["current"]
        assert FileStatementStore(field).get("surface.v1").content_utf8 == "原文按层展开。"
    counts = meter.summary(include_files)
    if operation != "surface_first_page":
        assert counts["categories"]["access_recovery_journal"]["write_bytes"] > 0
        if FileHandleStore(field).is_paged:
            assert counts["categories"]["core_recovery_journal"]["write_bytes"] > 0
    return counts, result, _logical_state(field)


def probe(remote_count=256, body_bytes=8192, *, include_files=False):
    if remote_count < 1 or body_bytes < 128:
        raise ValueError("remote_count must be positive and body_bytes at least 128")
    operations = ("surface_first_page", "new_at_known_cell", "revision_observed", "revision_by_statement_id")
    rows, fixtures = [], []
    with TemporaryDirectory(prefix="nollm-local-io-") as temporary:
        root = Path(temporary)
        _check_meter(root / "meter-check")
        for count in (0, remote_count):
            legacy, paged = root / f"legacy-{count}", root / f"paged-{count}"
            fixtures.append(_seed(legacy, count, body_bytes))
            shutil.copytree(legacy, paged)
            with CoreRuntime(paged) as core:
                core.enable_paged_storage(partition_width=WIDTH)
            FileHandleStore(paged).enable_paged_storage(partition_width=WIDTH)
            assert _logical_state(legacy) == _logical_state(paged), "migration changed logical field"
            for operation in operations:
                accepted_result = accepted_state = None
                for layout, source in (("legacy", legacy), ("paged", paged)):
                    field = root / f"run-{count}-{operation}-{layout}"
                    shutil.copytree(source, field)
                    counts, result, logical = _run_operation(field, operation, include_files)
                    if accepted_result is not None:
                        assert result == accepted_result, f"layout changed operation result: {operation}"
                        assert logical == accepted_state, f"layout changed final logical state: {operation}"
                    accepted_result, accepted_state = result, logical
                    rows.append({"remote_facts": count, "layout": layout, "operation": operation, **counts})
                    shutil.rmtree(field)
    return {
        "schema_version": "nollm_local_storage_cost_v1", "measurement": "application_file_api_payload_bytes",
        "fixture": fixtures, "logical_equivalence_checked": True,
        "method": {
            "intercepted": ["builtins.open", "io.open"], "fresh_runtime_per_operation": True,
            "includes": ["Core and Access file reads", "immutable Statement capture", "atomic temporary writes",
                         "Access and Core undo journal writes", "observed revision validation and readback"],
            "excludes": ["fixture creation", "migration", "copying", "cursor preparation", "post-measurement checks",
                         "directory and stat metadata", "fsync and rename device traffic", "OS cache and physical I/O"],
            "files": "distinct successfully accessed paths; atomic temporary files count as writes",
            "text_bytes": "decoded text re-encoded using the stream encoding; all fixture stores use UTF-8",
        },
        "limits": [
            "Same current code is used for both layouts; this is a layout comparison, not a historical release comparison.",
            "The fixed Surface and local target are on L-2; unrelated payload growth is remote L0 in different width-64 partitions.",
            "A touched page includes all its cells; same-page unrelated data can increase reads, writes and journal bytes.",
            "Surface still inventories occupancy metadata for its declared physical layers; more Surface cells can increase work.",
            "Binding lookup by Statement ID inventories binding pages; observed-handle revision avoids that lookup.",
            "Whole-layer budgets and explicit global export/inventory have their declared broader scope.",
            "This fixture has no bridges; Core opening currently reads the complete bridges file.",
            "No timings or physical-disk speedup claim are produced.",
        ],
        "operations": rows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote-count", type=int, default=256)
    parser.add_argument("--body-bytes", type=int, default=8192)
    parser.add_argument("--include-files", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.output is not None and args.output.exists():
        parser.error("choose a new output file")
    result = probe(args.remote_count, args.body_bytes, include_files=args.include_files)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(payload)
        print(json.dumps({"output": str(args.output.resolve()), "rows": len(result["operations"]),
                          "logical_equivalence_checked": True}))


if __name__ == "__main__":
    main()
