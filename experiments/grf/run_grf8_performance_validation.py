"""Windows-reproducible GRF8 before/after performance comparisons."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from time import perf_counter_ns

from nollm.grf.cell_address import CellAddress
from nollm.grf.facade import GRFFacade
from nollm.grf.global_field import GlobalFieldDirectory, partition_descriptor


def _ms(value: int) -> float:
    return round(value / 1_000_000, 3)


def _comparison(before_ns: int, after_ns: int, correct: bool) -> dict[str, object]:
    return {"before_ms": _ms(before_ns), "after_ms": _ms(after_ns), "improvement_percent": round((before_ns - after_ns) * 100 / before_ns, 2), "correctness_diff": not correct}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nollm-grf8-perf-") as temp:
        root = Path(temp)
        source = root / "facts.jsonl"
        source.write_text("".join(f'{{"fact":"{index}"}}\n' for index in range(200)), encoding="utf-8")
        facade = GRFFacade(root / "workspace")
        started = perf_counter_ns(); first = facade.capture_source(source, "2026-07-11T00:00:00Z"); full = perf_counter_ns() - started
        started = perf_counter_ns(); reload = facade.capture_source(source, "2026-07-11T00:00:01Z"); incremental = perf_counter_ns() - started
        started = perf_counter_ns(); placed = facade.place_batch(first.created_shards[:20], "window:perf", {"policy_id": "grf_deterministic_policy_v1"}, "2026-07-11T00:00:02Z"); batch = perf_counter_ns() - started
        started = perf_counter_ns(); snapshot = facade.snapshot(root / "snapshot"); restored = GRFFacade.restore(snapshot, root / "restored"); restore = perf_counter_ns() - started

        descriptors = tuple(partition_descriptor(f"partition:perf:{index}", index * 10, index * 10 + 9, index * 100, index * 100 + 99) for index in range(400))
        started = perf_counter_ns(); naive_directory = GlobalFieldDirectory()
        for descriptor in descriptors:
            naive_directory.add(descriptor)
        incremental_directory_build = perf_counter_ns() - started
        started = perf_counter_ns(); indexed_directory = GlobalFieldDirectory(); indexed_directory.add_many(descriptors); bulk_directory_build = perf_counter_ns() - started
        cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, 1234, 0)
        started = perf_counter_ns(); naive_hits = tuple(item.partition_id for item in descriptors if item.boundary.contains_cell(cell)); naive_lookup = perf_counter_ns() - started
        started = perf_counter_ns(); indexed_hits = indexed_directory.locate_cell(cell); indexed_lookup = perf_counter_ns() - started

        comparisons = {
            "unchanged_incremental_ingest": _comparison(full, incremental, reload.unchanged and not reload.created_shards),
            "bulk_directory_build": _comparison(incremental_directory_build, bulk_directory_build, naive_directory.digest() == indexed_directory.digest()),
            "indexed_cell_lookup": _comparison(naive_lookup, indexed_lookup, naive_hits == indexed_hits),
        }
        payload = {
            "comparisons": comparisons,
            "full_ingest_ms": _ms(full), "unchanged_incremental_ms": _ms(incremental), "batch_place_ms": _ms(batch), "snapshot_restore_ms": _ms(restore),
            "incremental_avoids_new_shards": reload.unchanged, "batch_correct": all(item.placement_record for item in placed),
            "snapshot_correct": bool(restored.validate_workspace().evidence_shard_count), "source_fallback_correct": all(facade.get_source(shard) for shard in first.created_shards),
        }
    passed = all(item["improvement_percent"] > 0 and not item["correctness_diff"] for item in comparisons.values()) and all(payload[key] for key in ("incremental_avoids_new_shards", "batch_correct", "snapshot_correct", "source_fallback_correct"))
    print(json.dumps(payload, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
