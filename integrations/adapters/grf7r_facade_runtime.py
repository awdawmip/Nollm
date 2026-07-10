"""Durable host ownership wrapper around the public GRF Host Contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
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


class HostRequestRegistryError(RuntimeError):
    pass


@dataclass(frozen=True)
class HostRequestRegistryEntry:
    host_request_id: str
    owner_host: str
    request_digest: str
    contract_version: str
    capability: str
    commit_state: str
    evidence_identity: str | None
    placement_identity: str | None
    admission_identity: str | None
    response_digest: str | None
    recorded_at: str

    def to_mapping(self) -> dict[str, object]:
        return {"schema": "grf7r2_host_request_registry_v1", **self.__dict__}

    @classmethod
    def from_mapping(cls, payload: dict[str, object]) -> "HostRequestRegistryEntry":
        if payload.get("schema") != "grf7r2_host_request_registry_v1":
            raise HostRequestRegistryError("host request registry schema mismatch")
        values = {name: payload.get(name) for name in cls.__dataclass_fields__}
        if any(not isinstance(values[name], str) or not values[name] for name in ("host_request_id", "owner_host", "request_digest", "contract_version", "capability", "commit_state", "recorded_at")):
            raise HostRequestRegistryError("host request registry entry is incomplete")
        if values["commit_state"] not in ("prepared", "committed"):
            raise HostRequestRegistryError("host request registry commit_state is invalid")
        for name in ("evidence_identity", "placement_identity", "admission_identity", "response_digest"):
            if values[name] is not None and not isinstance(values[name], str):
                raise HostRequestRegistryError("host request registry identity is invalid")
        return cls(**values)  # type: ignore[arg-type]


class HostRequestRegistry:
    """Adapter-owned durable ownership and retry metadata, never Core truth."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._entries: dict[str, HostRequestRegistryEntry] = {}
        self.truncated_tail_detected = False
        self._load()

    def get(self, request_id: str) -> HostRequestRegistryEntry | None:
        return self._entries.get(request_id)

    def record(self, entry: HostRequestRegistryEntry) -> None:
        previous = self._entries.get(entry.host_request_id)
        if previous is not None:
            if (previous.owner_host, previous.request_digest, previous.contract_version, previous.capability) != (entry.owner_host, entry.request_digest, entry.contract_version, entry.capability):
                raise HostRequestRegistryError("host request registry ownership conflict")
            if previous.commit_state == "committed" and entry.commit_state != "committed":
                raise HostRequestRegistryError("host request registry cannot regress committed state")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(entry.to_mapping(), sort_keys=True, separators=(",", ":")) + "\n")
            stream.flush()
        self._entries[entry.host_request_id] = entry

    def snapshot(self) -> dict[str, object]:
        payload = tuple(self._entries[key].to_mapping() for key in sorted(self._entries))
        return {"entry_count": len(payload), "digest": sha256(canonical_dumps(payload)).hexdigest(), "truncated_tail_detected": self.truncated_tail_detected}

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = self.path.read_bytes()
        if not payload:
            return
        lines = payload.splitlines(keepends=True)
        for index, line in enumerate(lines):
            is_tail = index == len(lines) - 1 and not line.endswith(b"\n")
            if is_tail:
                self.truncated_tail_detected = True
                break
            try:
                entry = HostRequestRegistryEntry.from_mapping(json.loads(line))
            except (json.JSONDecodeError, TypeError, HostRequestRegistryError) as exc:
                raise HostRequestRegistryError(f"host request registry corruption at line {index + 1}") from exc
            previous = self._entries.get(entry.host_request_id)
            if previous is not None and (previous.owner_host, previous.request_digest, previous.contract_version, previous.capability) != (entry.owner_host, entry.request_digest, entry.contract_version, entry.capability):
                raise HostRequestRegistryError("host request registry contains conflicting durable ownership")
            if previous is not None and previous.commit_state == "committed" and entry.commit_state == "prepared":
                raise HostRequestRegistryError("host request registry contains commit-state regression")
            self._entries[entry.host_request_id] = entry


class FacadeRuntimeAdapter:
    """Contract adapter with durable ownership; Core files remain the facts."""

    def __init__(self, workspace: Path, ledger_path: Path, *, registry_path: Path | None = None, compact_ledger: bool = False) -> None:
        self.workspace = Path(workspace)
        self.service = GRFHostService(self.workspace)
        self.store = GRFFileStore(self.workspace)
        self.ledger_path = Path(ledger_path)
        self.registry = HostRequestRegistry(registry_path or self.ledger_path.with_name("host_request_registry.jsonl"))
        self.compact_ledger = compact_ledger
        self.responses: dict[str, dict[str, object]] = {}
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
        durable = self.registry.get(request_id)
        if durable is not None:
            if durable.owner_host != host_name:
                return self._error(request, "cross_host_or_mutated_replay", started)
            if durable.request_digest != digest:
                return self._error(request, "cross_host_or_mutated_replay", started)
            if request_id in self.responses:
                return self._finish(host_name, request, self.responses[request_id], started, recovered=False, cache_hit=True)
            if durable.commit_state == "committed" and request.capability in ("capture", "place", "admit"):
                try:
                    recovered = self._recover_committed(request)
                except (TypeError, ValueError):
                    return self._error(request, "durable_replay_mismatch", started)
                if recovered is None:
                    return self._error(request, "durable_commit_missing_core_record", started)
                return self._finish(host_name, request, recovered, started, recovered=True)
        elif request.capability in ("capture", "place", "admit") and self._core_record_exists(request):
            return self._error(request, "ownership_unverifiable", started)
        else:
            self.registry.record(_registry_entry(host_name, request, digest, "prepared"))
        if self.fail_before_dispatch:
            self.fail_before_dispatch = False
            raise RuntimeError("injected adapter crash")
        response = self.service.handle(request).to_mapping()
        if response.get("ok") is True and (durable is None or request.capability in ("capture", "place", "admit")):
            self.registry.record(_registry_entry(host_name, request, digest, "committed", response))
        return self._finish(host_name, request, response, started, recovered=False, lose_response_after_commit=lose_response_after_commit)

    def _finish(self, host_name: str, request: GRFHostRequest, response: dict[str, object], started: int, *, recovered: bool, cache_hit: bool = False, lose_response_after_commit: bool = False) -> dict[str, object]:
        response = dict(response)
        response["adapter_latency_ns"] = perf_counter_ns() - started
        self._append_event(host_name, request, response, recovered, cache_hit)
        if self.partial_after_dispatch:
            self.partial_after_dispatch = False
            return {"contract_version": request.contract_version, "host_request_id": request.host_request_id.value, "ok": False, "error_code": "partial_response_rejected"}
        if lose_response_after_commit:
            raise LostHostResponse(request.host_request_id.value)
        self.responses[request.host_request_id.value] = response
        return response

    def _core_record_exists(self, request: GRFHostRequest) -> bool:
        try:
            if request.capability == "capture":
                capture_id = str(request.payload["capture_id"])
                self.store.read_evidence_shard("shard:grf:" + sha256(capture_id.encode("utf-8")).hexdigest()[:24])
                return True
            if request.capability == "place" and request.evidence_identity is not None:
                self.store.read_placement_record(_placement_id(request.evidence_identity.value))
                return True
            if request.capability == "admit" and request.evidence_identity is not None:
                self.store.read_minimal_admission_record(_admission_id(request.evidence_identity.value))
                return True
        except FileNotFoundError:
            return False
        return False

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
        return {"contract_version": request.contract_version, "host_request_id": request.host_request_id.value, "capability": request.capability, "ok": True, "result": {"recovered_from_core": True}, "error_code": None, "evidence_identity": evidence, "placement_identity": placement, "admission_identity": admission, "core_latency_ns": 0}

    def _error(self, request: GRFHostRequest, code: str, started: int) -> dict[str, object]:
        return {"contract_version": request.contract_version, "host_request_id": request.host_request_id.value, "capability": request.capability, "ok": False, "result": None, "error_code": code, "adapter_latency_ns": perf_counter_ns() - started}

    def _append_event(self, host: str, request: GRFHostRequest, response: dict[str, object], recovered: bool, cache_hit: bool = False) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if self.compact_ledger:
            event = {"host": host, "host_request_id": request.host_request_id.value, "capability": request.capability, "request_sha256": sha256(canonical_dumps(request.to_mapping())).hexdigest(), "ok": response.get("ok"), "error_code": response.get("error_code"), "recovered_from_core": recovered, "cache_hit": cache_hit, "evidence_identity": response.get("evidence_identity"), "placement_identity": response.get("placement_identity"), "admission_identity": response.get("admission_identity")}
        else:
            event = {"host": host, "request": request.to_mapping(), "response": response, "recovered_from_core": recovered}
        if self._ledger_stream is None:
            self._ledger_stream = self.ledger_path.open("a", encoding="utf-8", newline="\n")
        self._ledger_stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")


def _registry_entry(host: str, request: GRFHostRequest, digest: str, commit_state: str, response: dict[str, object] | None = None) -> HostRequestRegistryEntry:
    response = response or {}
    return HostRequestRegistryEntry(request.host_request_id.value, host, digest, request.contract_version, request.capability, commit_state, _text(response.get("evidence_identity")), _text(response.get("placement_identity")), _text(response.get("admission_identity")), None if not response else sha256(canonical_dumps(response)).hexdigest(), datetime.now(timezone.utc).isoformat())


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _placement_id(shard_id: str) -> str:
    return "placement:grf1ik:" + sha256(shard_id.encode("utf-8")).hexdigest()[:24]


def _admission_id(shard_id: str) -> str:
    return "admission:grf1ik:" + sha256(shard_id.encode("utf-8")).hexdigest()[:24]
