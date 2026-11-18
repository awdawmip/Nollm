"""Time warm Access recall on 64 real bindings, with seven cells in range.

Run the same script with PYTHONPATH pointing to each revision's Core/Access src.
The field is temporary; setup, warmup and instrumented calls are outside timing.
"""
import argparse
from dataclasses import asdict
from hashlib import sha256
import json
from math import ceil
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from time import perf_counter_ns
from unittest.mock import patch

from nollm_access import AccessDecision, AccessRecallRequest, AccessRuntime, FileHandleStore
from nollm_access import FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress, RecallBudget


NEAR = ((0, 0), (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1))


def cell(q, r):
    return GeometryAddress("default_dream_v1", "default", 0, q, r)


def registry_io(access, request):
    path = access.handle_store.path
    raw = path.read_text(encoding="utf-8")
    reads = decodes = 0
    read_bytes, loads = Path.read_bytes, json.loads

    def counted_read(file):
        nonlocal reads
        reads += file == path
        return read_bytes(file)

    def counted_loads(document, *args, **kwargs):
        nonlocal decodes
        decodes += document == raw
        return loads(document, *args, **kwargs)

    with patch.object(Path, "read_bytes", counted_read), patch.object(json, "loads", counted_loads):
        result = access.recall(request)
    wire = json.dumps(asdict(result), sort_keys=True, separators=(",", ":")).encode()
    return {"binding_reads": reads, "binding_json_decodes": decodes,
            "items": len(result.items), "result_sha256": sha256(wire).hexdigest()}


def measure(root, rounds):
    with CoreRuntime(root) as core, AccessRuntime(
            core, FileStatementStore(root), FileHandleStore(root)) as access:
        for i in range(64):
            position = NEAR[i] if i < len(NEAR) else (2 * i, 0)
            key = f"note-{i:02d}"
            access.put_statement(MemoryStatement(key, f"Source evidence {i}"))
            access.apply(AccessDecision(key, key, "new", target_cell=cell(*position),
                                        reason_text="Deterministic benchmark placement."))

    request = AccessRecallRequest("bounded-access", entry_cells=(cell(0, 0),),
                                  allowed_kernels=("lateral",), budget=RecallBudget(1, 8, 0, 1, 0, 7))
    with CoreRuntime(root) as core, AccessRuntime(
            core, FileStatementStore(root), FileHandleStore(root)) as access:
        output = registry_io(access, request)
        if output["items"] != len(NEAR):
            raise RuntimeError("unexpected geometric neighborhood")
        samples = []
        for _ in range(rounds):
            start = perf_counter_ns()
            access.recall(request)
            samples.append((perf_counter_ns() - start) / 1_000_000)
    return {**output, "rounds": rounds, "median_ms": median(samples),
            "p95_ms": sorted(samples)[ceil(0.95 * len(samples)) - 1]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=50)
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error("--rounds must be positive")
    with TemporaryDirectory() as directory:
        print(json.dumps(measure(Path(directory), args.rounds), indent=2))
