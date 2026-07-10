"""Real-file GRF8 placement and admission workflow validation."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from nollm.grf.facade import GRFFacade
from nollm.grf.grf7_incremental_validation import run_incremental_repartition_validation


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nollm-grf8-admission-") as temp:
        root = Path(temp)
        source = root / "facts.jsonl"
        source.write_text('{"fact":"one"}\n{"fact":"two"}\n{"fact":"three"}\n', encoding="utf-8")
        facade = GRFFacade(root / "workspace")
        ingested = facade.capture_source(source, "2026-07-11T00:00:00Z")
        first, *rest = ingested.created_shards
        manual = facade.place(first, "window:manual", {"policy_id": "validation_fixture_policy", "target_cell": {"profile_id": "eisenstein_exact_v1", "chart_id": "chart:manual", "layer": 0, "q": 1, "r": 1}}, "2026-07-11T00:00:01Z")
        rule = facade.place(rest[0], "window:rule", {"policy_id": "grf_deterministic_policy_v1"}, "2026-07-11T00:00:01Z")
        batched = facade.place_batch(tuple(rest[1:]), "window:batch", {"policy_id": "grf_deterministic_policy_v1"}, "2026-07-11T00:00:01Z")
        admissions = (facade.admit_existing_placement(first, manual.placement_record.placement_id, "2026-07-11T00:00:02Z", "human"), facade.admit_existing_placement(rest[0], rule.placement_record.placement_id, "2026-07-11T00:00:02Z", "host_rule"), *facade.admit_batch(tuple((item.placement_record.shard_id, item.placement_record.placement_id) for item in batched), "2026-07-11T00:00:02Z", "batch_explicit"))
        replacement = facade.re_place(first, "window:manual", {"policy_id": "grf_deterministic_policy_v1", "chart_id": "chart:replacement"}, "replacement:1", "2026-07-11T00:00:03Z")
        incremental = run_incremental_repartition_validation()
        result = {
            "capture_place_admit": len(admissions) == len(ingested.created_shards),
            "place_is_not_admit": manual.admission_record is None and manual.placement_record is not None,
            "distinct_admissions": len({item.admission_id for item in admissions}) == len(admissions),
            "batch_preserves_evidence_identity": len({item.placement_record.shard_id for item in batched}) == len(batched),
            "incremental_equals_full_rebuild": incremental.incremental_equals_full_rebuild,
            "replacement_preserves_source": replacement.placement_record.placement_id != manual.placement_record.placement_id and bool(facade.get_source(first)),
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if all(result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
