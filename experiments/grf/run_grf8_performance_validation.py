from __future__ import annotations
import json, tempfile
from pathlib import Path
from time import perf_counter_ns
from nollm.grf.facade import GRFFacade

def _ms(value: int) -> float: return round(value / 1_000_000, 3)
def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nollm-grf8-perf-") as temp:
        root=Path(temp); source=root/"facts.jsonl"; source.write_text("".join(f'{{"fact":"{i}"}}\n' for i in range(200)),encoding="utf-8")
        facade=GRFFacade(root/"workspace")
        started=perf_counter_ns(); first=facade.capture_source(source,"2026-07-11T00:00:00Z"); full=perf_counter_ns()-started
        started=perf_counter_ns(); reload=facade.capture_source(source,"2026-07-11T00:00:01Z"); incremental=perf_counter_ns()-started
        started=perf_counter_ns(); placed=facade.place_batch(first.created_shards[:20],"window:perf",{"policy_id":"grf_deterministic_policy_v1"},"2026-07-11T00:00:02Z"); batch=perf_counter_ns()-started
        payload={"full_ingest_ms":_ms(full),"unchanged_incremental_ms":_ms(incremental),"batch_place_ms":_ms(batch),"incremental_avoids_new_shards":reload.unchanged,"batch_correct":all(item.placement_record for item in placed),"source_fallback_correct":all(facade.get_source(shard) for shard in first.created_shards)}
    print(json.dumps(payload,sort_keys=True)); return 0 if all(payload[key] for key in ("incremental_avoids_new_shards","batch_correct","source_fallback_correct")) else 1
if __name__ == "__main__": raise SystemExit(main())
