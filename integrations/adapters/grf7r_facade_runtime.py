"""Trusted runtime wrapper around the public GRF Host Contract and Facade."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter_ns
from typing import Any

from nollm.grf.host_contract import GRFHostRequest, GRFHostService
from nollm.grf.json_canonical import canonical_dumps
from nollm.grf.storage import GRFFileStore


class LostHostResponse(TimeoutError):
    pass


class FacadeRuntimeAdapter:
    """Adds host ownership and retry assistance without owning Core facts."""

    def __init__(self, workspace: Path, ledger_path: Path, *, compact_ledger: bool = False) -> None:
        self.workspace = Path(workspace)
        self.service = GRFHostService(self.workspace)
        self.store = GRFFileStore(self.workspace)
        self.ledger_path = Path(ledger_path)
        self.compact_ledger = compact_ledger
        self.responses: dict[str, dict[str, object]] = {}
        self.request_owners: dict[str, tuple[str, str]] = {}
        self.fail_before_dispatch = False
        self.partial_after_dispatch = False
        self._ledger_stream = None

    def clear_response_cache(self) -> None:
        self.responses.clear()

    def flush_events(self) -> None:
        if self._ledger_stream is not None:
            self._ledger_stream.flush()

    def close(self) -> None:
        if self._ledger_stream is not None:
            self._ledger_stream.close()
            self._ledger_stream = None

    def handle(self, host_name: str, mapping: dict[str, Any], *, lose_response_after_commit: bool = False) -> dict[str, object]:
        started = perf_counter_ns()
        request = GRFHostRequest.from_mapping(mapping)
        request_id = request.host_request_id.value
        digest = sha256(canonical_dumps(request.to_mapping())).hexdigest()
        owner = self.request_owners.get(request_id)
        if owner is not None and owner != (host_name, digest):
            return self._error(request, "cross_host_or_mutated_replay", started)
        self.request_owners.setdefault(request_id, (host_name, digest))
        if request_id in self.responses:
            return self.responses[request_id]
        if self.fail_before_dispatch:
            self.fail_before_dispatch = False
            raise RuntimeError("injected adapter crash")
        try:
            recovered = self._recover_committed(request)
        except (TypeError, ValueError):
            return self._error(request, "durable_replay_mismatch", started)
        response = recovered if recovered is not None else self.service.handle(request).to_mapping()
        response["adapter_latency_ns"] = perf_counter_ns() - started
        self._append_event(host_name, request, response, recovered is not None)
        if self.partial_after_dispatch:
            self.partial_after_dispatch = False
            return {"contract_version": request.contract_version, "host_request_id": request_id, "ok": False, "error_code": "partial_response_rejected"}
        if lose_response_after_commit:
            raise LostHostResponse(request_id)
        self.responses[request_id] = response
        return response

    def _recover_committed(self, request: GRFHostRequest) -> dict[str, object] | None:
        payload = request.payload
        try:
            if request.capability == "capture":
                capture_id = str(payload["capture_id"])
                shard_id = "shard:grf:" + sha256(capture_id.encode("utf-8")).hexdigest()[:24]
                shard = self.store.read_evidence_shard(shard_id)
                if shard.content != payload.get("content") or tuple(payload.get("source_window_refs", ())) != shard.source_window_refs:
                    raise ValueError("capture replay does not match durable evidence")
                return self._recovered(request, shard_id, None, None)
            if request.capability == "place" and request.evidence_identity is not None:
                placement_id = _placement_id(request.evidence_identity.value)
                placement = self.store.read_placement_record(placement_id)
                if placement.shard_id != request.evidence_identity.value:
                    raise ValueError("placement replay identity mismatch")
                return self._recovered(request, placement.shard_id, placement.placement_id, None)
            if request.capability == "admit" and request.evidence_identity is not None and request.placement_identity is not None:
                admission_id = _admission_id(request.evidence_identity.value)
                admission = self.store.read_minimal_admission_record(admission_id)
                if admission.placement_record.placement_id != request.placement_identity.value:
                    raise ValueError("admission replay placement mismatch")
                return self._recovered(request, admission.shard_id, admission.placement_record.placement_id, admission.admission_id)
        except FileNotFoundError:
            return None
        return None

    def _recovered(self, request: GRFHostRequest, evidence: str | None, placement: str | None, admission: str | None) -> dict[str, object]:
        return {
            "contract_version": request.contract_version,
            "host_request_id": request.host_request_id.value,
            "capability": request.capability,
            "ok": True,
            "result": {"recovered_from_core": True},
            "error_code": None,
            "evidence_identity": evidence,
            "placement_identity": placement,
            "admission_identity": admission,
            "core_latency_ns": 0,
        }

    def _error(self, request: GRFHostRequest, code: str, started: int) -> dict[str, object]:
        return {
            "contract_version": request.contract_version,
            "host_request_id": request.host_request_id.value,
            "capability": request.capability,
            "ok": False,
            "result": None,
            "error_code": code,
            "adapter_latency_ns": perf_counter_ns() - started,
        }

    def _append_event(self, host: str, request: GRFHostRequest, response: dict[str, object], recovered: bool) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if self.compact_ledger:
            event = {
                "host": host,
                "host_request_id": request.host_request_id.value,
                "capability": request.capability,
                "request_sha256": sha256(canonical_dumps(request.to_mapping())).hexdigest(),
                "ok": response.get("ok"),
                "error_code": response.get("error_code"),
                "recovered_from_core": recovered,
            }
        else:
            event = {"host": host, "request": request.to_mapping(), "response": response, "recovered_from_core": recovered}
        if self._ledger_stream is None:
            self._ledger_stream = self.ledger_path.open("a", encoding="utf-8", newline="\n")
        self._ledger_stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")


def _placement_id(shard_id: str) -> str:
    return "placement:grf1ik:" + sha256(shard_id.encode("utf-8")).hexdigest()[:24]


def _admission_id(shard_id: str) -> str:
    return "admission:grf1ik:" + sha256(shard_id.encode("utf-8")).hexdigest()[:24]
