"""Exercise the complete GRF8 contract lifecycle against each host fixture."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from integrations.adapters.grf7r2_long_running import _admit_request, _capture_request, _place_request, _query_request
from integrations.adapters.grf7r_facade_runtime import FacadeRuntimeAdapter


def _request(request_id: str, capability: str, payload: dict[str, object], **identities: str | None) -> dict[str, object]:
    return {"contract_version": "grf_host_v2", "host_request_id": request_id, "capability": capability, "payload": payload, "evidence_identity": identities.get("evidence_identity"), "placement_identity": identities.get("placement_identity"), "admission_identity": identities.get("admission_identity")}


def _run_host(root: Path, host: str, index: int) -> dict[str, bool]:
    registry = root / f"{host}.registry.jsonl"
    adapter = FacadeRuntimeAdapter(root / host, root / f"{host}.events.jsonl", registry_path=registry)
    capture = _capture_request(index)
    capture["host_request_id"] = f"host:{host}:capture"
    captured = adapter.handle(host, capture)
    shard = str(captured.get("evidence_identity"))
    place = _place_request(index, shard)
    place["host_request_id"] = f"host:{host}:place"
    placed = adapter.handle(host, place)
    placement = str(placed.get("placement_identity"))
    admit = _admit_request(index, shard, placement)
    admit["host_request_id"] = f"host:{host}:admit"
    admitted = adapter.handle(host, admit)
    admission = str(admitted.get("admission_identity"))
    recall = adapter.handle(host, _query_request(f"host:{host}:recall", "recall", admission))
    source = adapter.handle(host, _request(f"host:{host}:source", "source_get", {}, evidence_identity=shard))
    path = root / f"{host}.txt"
    path.write_text("first source revision", encoding="utf-8")
    ingested = adapter.handle(host, _request(f"host:{host}:capture-source", "capture_source", {"path": str(path), "recorded_at": "2026-07-11T00:00:03Z"}))
    path.write_text("second source revision", encoding="utf-8")
    revised = adapter.handle(host, _request(f"host:{host}:revise", "revise", {"path": str(path), "recorded_at": "2026-07-11T00:00:04Z"}))
    source_id = str((ingested.get("result") or {}).get("source_id", ""))
    retired = adapter.handle(host, _request(f"host:{host}:retire", "retire", {"source_id": source_id}))
    adapter.close()
    restarted = FacadeRuntimeAdapter(root / host, root / f"{host}.events.jsonl", registry_path=registry)
    replay = restarted.handle(host, _query_request(f"host:{host}:replay", "replay", admission))
    restarted.close()
    return {
        "capture": captured.get("ok") is True,
        "place": placed.get("ok") is True,
        "admit": admitted.get("ok") is True,
        "recall": recall.get("ok") is True,
        "source_get": source.get("ok") is True and bool((source.get("result") or {}).get("content")),
        "capture_source": ingested.get("ok") is True and bool(source_id),
        "revise": revised.get("ok") is True,
        "retire": retired.get("ok") is True,
        "restart_replay": replay.get("ok") is True,
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nollm-grf8-host-") as temp:
        root = Path(temp)
        outcomes = {host: _run_host(root, host, index) for index, host in enumerate(("file_host", "codex_fixture", "openclaw_fixture"))}
    passed = all(all(values.values()) for values in outcomes.values())
    print(json.dumps({"hosts": outcomes, "all_contracts": passed}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
