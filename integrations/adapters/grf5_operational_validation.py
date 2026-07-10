"""Bounded long-running product Host validation with restarts and replay."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns

from .grf_product_host import GRFProductHost


@dataclass(frozen=True)
class OperationalResult:
    cycles: int
    restart_count: int
    evidence_count: int
    placement_count: int
    admission_count: int
    replay_deterministic: bool
    source_fallback_preserved: bool
    elapsed_ns: int


def run_operational_validation(workspace: Path, cycles: int = 250, restart_interval: int = 25) -> OperationalResult:
    if cycles < 1 or restart_interval < 1:
        raise ValueError("cycles and restart_interval must be positive")
    host = GRFProductHost(workspace, "operational")
    first_admission = first_shard = None
    restarts = 0
    started = perf_counter_ns()
    for index in range(cycles):
        if index and index % restart_interval == 0:
            host = host.restart()
            restarts += 1
        window = f"window:product:{index}"
        capture = host.capture(f"capture:product:{index}", f"product evidence {index}", window, "2026-07-10T00:00:00Z")
        shard = str(capture["evidence_identity"])
        place = host.place(shard, window, "2026-07-10T00:00:01Z")
        admission = host.admit(shard, str(place["placement_identity"]), "2026-07-10T00:00:02Z")
        if first_admission is None:
            first_admission = str(admission["admission_identity"])
            first_shard = shard
    before = host.recall("admission_id", first_admission, first_admission)
    host = host.restart()
    restarts += 1
    after = host.replay("admission_id", first_admission, first_admission)
    report = after["result"]["coverage_reports"][0]
    counts = host.validate()["result"]
    return OperationalResult(cycles, restarts, counts["evidence_shard_count"], counts["placement_record_count"], counts["admission_record_count"], before["result"] == after["result"], report["source_fallback_ref"] == first_shard, perf_counter_ns() - started)
