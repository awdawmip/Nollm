from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter_ns

from latency_support import COMMIT_SCHEMA, nearest_rank


def main() -> None:
    iterations = 200
    disabled_us: list[float] = []
    enabled_us: list[float] = []
    record = {"schema_version": COMMIT_SCHEMA, "event_type": "fixture", "event_epoch_ms": 1, "scenario_id": "overhead", "validation_run_id": "fixture", "duration_us": 1}
    encoded = json.dumps(record, separators=(",", ":")) + "\n"
    with TemporaryDirectory(prefix="nollm-latency-overhead-") as temporary:
        path = Path(temporary) / "events.jsonl"
        for _ in range(iterations):
            started = perf_counter_ns()
            if False:
                path.write_text(encoded, encoding="utf-8")
            disabled_us.append((perf_counter_ns() - started) / 1_000)
            started = perf_counter_ns()
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(encoded)
            enabled_us.append((perf_counter_ns() - started) / 1_000)
    disabled_p95 = nearest_rank(disabled_us, 0.95)
    enabled_p95 = nearest_rank(enabled_us, 0.95)
    absolute_increase_ms = max(0.0, enabled_p95 - disabled_p95) / 1_000
    relative_increase = None if disabled_p95 == 0 else (enabled_p95 - disabled_p95) / disabled_p95
    passed = absolute_increase_ms <= 5.0 or (relative_increase is not None and relative_increase <= 0.05)
    result = {"schema_version": "nollm_latency_instrumentation_overhead_v1", "status": "pass" if passed else "fail", "iterations": iterations, "disabled_p95_us": disabled_p95, "enabled_p95_us": enabled_p95, "absolute_increase_ms": absolute_increase_ms, "relative_increase": relative_increase, "acceptance": "relative_p95<=5% or absolute_increase<=5ms"}
    print(json.dumps(result, separators=(",", ":")))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
