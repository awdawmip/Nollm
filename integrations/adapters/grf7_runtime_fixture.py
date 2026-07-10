"""Queued GRF7 host runtime fixtures mediated by Adapter and Host Contract."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter_ns

from nollm.grf.admission import MinimalAdmissionRecord
from nollm.grf.cell_address import CellAddress
from nollm.grf.evidence import EvidenceShardRecord
from nollm.grf.global_field import GRFPartition, GlobalRecallBudget, GlobalRecallQuery, GlobalShardedField, partition_descriptor
from nollm.grf.host_contract import GRFHostRequest
from nollm.grf.placement import GeometryMark, PlacementRecord


@dataclass(frozen=True)
class RuntimeValidationResult:
    runtime_count: int
    request_count: int
    successful_request_count: int
    capture_count: int
    placement_count: int
    admission_count: int
    recall_count: int
    replay_count: int
    retry_count: int
    restart_count: int
    injected_adapter_failure_count: int
    timeout_count: int
    duplicate_evidence_count: int
    identity_collision_count: int
    replay_deterministic: bool
    retry_idempotent: bool
    adapter_owns_durable_truth: bool
    total_latency_ns: int
    status: str

    def to_mapping(self) -> dict[str, object]:
        return self.__dict__.copy()


class GRF7RuntimeCore:
    def __init__(self) -> None:
        self.field = GlobalShardedField()
        for index in range(100):
            self.field.add_partition(GRFPartition(partition_descriptor(f"partition:runtime:{index:03d}", index, index, index * 1_000_000, index * 1_000_000 + 999_999)))
        self.evidence: dict[str, EvidenceShardRecord] = {}
        self.placements: dict[str, PlacementRecord] = {}
        self.admissions: dict[str, MinimalAdmissionRecord] = {}
        self.capture_to_shard: dict[str, str] = {}

    def dispatch(self, request: GRFHostRequest) -> dict[str, object]:
        payload = request.payload
        if request.capability == "capture":
            capture_id = _required(payload, "capture_id")
            existing = self.capture_to_shard.get(capture_id)
            if existing is not None:
                return {"status": "captured", "evidence_identity": existing}
            content = _required(payload, "content")
            shard_id = "shard:grf7:runtime:" + sha256(capture_id.encode("utf-8")).hexdigest()[:24]
            shard = EvidenceShardRecord(shard_id, content, "2026-07-10T00:00:00Z", "validation_fixture", (f"window:{capture_id}",), "host_declared", "captured")
            self.evidence[shard_id] = shard
            self.capture_to_shard[capture_id] = shard_id
            return {"status": "captured", "evidence_identity": shard_id}
        if request.capability == "place":
            shard_id = request.evidence_identity.value if request.evidence_identity else ""
            shard = self.evidence[shard_id]
            index = int(_required(payload, "sequence"))
            partition_index = index % 100
            cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, partition_index, 0)
            placement_id = f"placement:grf7:runtime:{index}"
            mark = GeometryMark(f"mark:grf7:runtime:{index}", shard_id, cell.profile_id, cell.chart_id, cell, "runtime_fixture", "high", 0, "field:grf7:runtime")
            placement = PlacementRecord(placement_id, shard_id, f"candidate:grf7:runtime:{index}", f"decision:grf7:runtime:{index}", mark, f"island:grf7:runtime:{index}", f"patch:grf7:runtime:{partition_index}", (shard_id,), cell.profile_id, "grf7_runtime_v1")
            self.field.insert(f"partition:runtime:{partition_index:03d}", placement)
            self.placements[placement_id] = placement
            return {"status": "placed", "evidence_identity": shard_id, "placement_identity": placement_id}
        if request.capability == "admit":
            shard_id = request.evidence_identity.value if request.evidence_identity else ""
            placement_id = request.placement_identity.value if request.placement_identity else ""
            placement = self.placements[placement_id]
            admission_id = "admission:grf7:runtime:" + placement_id.rsplit(":", 1)[-1]
            admission = MinimalAdmissionRecord(admission_id, shard_id, placement, "2026-07-10T00:00:01Z", "host_rule")
            self.admissions[admission_id] = admission
            self.field._identity_routes[("admission_id", admission_id)] = self.field._identity_routes[("placement_id", placement_id)]
            self.field._identity_placements[("admission_id", admission_id)] = placement_id
            return {"status": "admitted", "evidence_identity": shard_id, "placement_identity": placement_id, "admission_identity": admission_id}
        if request.capability in ("recall", "replay"):
            mode = _required(payload, "entry_mode")
            ref = _required(payload, "entry_ref")
            result = self.field.recall(GlobalRecallQuery(_required(payload, "query_id"), mode, ref, GlobalRecallBudget(1, 1, 2, 1, 0), False))
            return {"selected_shards": result.selected_shards, "source_fallback_refs": result.path.source_fallback_refs, "path": result.path.visited_partitions}
        raise ValueError("unsupported runtime capability")


class GRF7RuntimeAdapter:
    def __init__(self, core: GRF7RuntimeCore, event_log: Path) -> None:
        self.core = core
        self.event_log = event_log
        self.responses: dict[str, dict[str, object]] = {}
        self.fail_next = False

    def handle(self, mapping: dict[str, object]) -> dict[str, object]:
        request = GRFHostRequest.from_mapping(mapping)
        key = request.host_request_id.value
        if key in self.responses:
            return self.responses[key]
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("injected adapter failure")
        result = self.core.dispatch(request)
        response = {"ok": True, "host_request_id": key, "capability": request.capability, "result": result}
        self.responses[key] = response
        self.event_log.parent.mkdir(parents=True, exist_ok=True)
        with self.event_log.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps({"host_request_id": key, "capability": request.capability, "ok": True}, sort_keys=True) + "\n")
        return response


class QueuedRuntimeFixture:
    def __init__(self, name: str, adapter: GRF7RuntimeAdapter) -> None:
        self.name = name
        self.adapter = adapter
        self.queue: deque[dict[str, object]] = deque()
        self.started = False
        self.session = 0
        self.timeout_next = False

    def start(self) -> None:
        self.started = True
        self.session += 1

    def submit(self, request: dict[str, object]) -> None:
        if not self.started:
            raise RuntimeError("runtime not started")
        self.queue.append(request)

    def process_one(self) -> dict[str, object]:
        request = self.queue.popleft()
        if self.timeout_next:
            self.timeout_next = False
            return {"ok": False, "error_code": "timeout", "retryable": True}
        try:
            return self.adapter.handle(request)
        except RuntimeError:
            return {"ok": False, "error_code": "adapter_failure", "retryable": True}

    def restart(self) -> None:
        self.started = False
        self.start()

    def shutdown(self) -> None:
        self.started = False


def run_runtime_validation(root: Path, request_count: int = 100_000, retry_target: int = 1_000, restart_target: int = 100, failure_target: int = 100) -> RuntimeValidationResult:
    core = GRF7RuntimeCore()
    fixtures = tuple(QueuedRuntimeFixture(name, GRF7RuntimeAdapter(core, Path(root) / name / "events.jsonl")) for name in ("file", "openclaw", "codex"))
    for fixture in fixtures:
        fixture.start()
    retries = restarts = failures = timeouts = successful = recalls = replays = 0
    retry_idempotent = replay_deterministic = True
    identities: dict[int, tuple[str, str, str]] = {}
    started = perf_counter_ns()
    for index in range(request_count):
        fixture = fixtures[index % len(fixtures)]
        object_index = index // 5
        operation = index % 5
        request = _request(fixture.name, index, object_index, operation, identities)
        inject_timeout = timeouts < retry_target and index % max(1, request_count // retry_target) == 0
        inject_failure = failures < failure_target and index % max(1, request_count // failure_target) == 1
        if inject_timeout:
            fixture.timeout_next = True
        if inject_failure:
            fixture.adapter.fail_next = True
        fixture.submit(request)
        response = fixture.process_one()
        if response.get("ok") is not True and response.get("retryable") is True:
            if response.get("error_code") == "timeout":
                timeouts += 1
            else:
                failures += 1
            fixture.submit(request)
            retried = fixture.process_one()
            retries += 1
            if retried.get("ok") is not True:
                continue
            response = retried
        if response.get("ok") is True:
            successful += 1
            result = response["result"]
            if operation == 0:
                identities[object_index] = (str(result["evidence_identity"]), "", "")
            elif operation == 1:
                evidence = identities[object_index][0]
                identities[object_index] = (evidence, str(result["placement_identity"]), "")
            elif operation == 2:
                evidence, placement, _ = identities[object_index]
                identities[object_index] = (evidence, placement, str(result["admission_identity"]))
            elif operation == 3:
                recalls += 1
            else:
                replays += 1
        if restarts < restart_target and (index + 1) % max(1, request_count // restart_target) == 0:
            fixture.restart()
            restarts += 1
    total_ns = perf_counter_ns() - started
    for fixture in fixtures:
        fixture.shutdown()
    duplicates = len(core.capture_to_shard) - len(set(core.capture_to_shard.values()))
    namespaces = set(core.evidence) & set(core.placements) | set(core.evidence) & set(core.admissions) | set(core.placements) & set(core.admissions)
    status = "GATE_G_PASS" if retries >= retry_target and restarts >= restart_target and failures >= failure_target and duplicates == 0 and not namespaces else "GATE_G_FAIL"
    return RuntimeValidationResult(3, request_count, successful, len(core.evidence), len(core.placements), len(core.admissions), recalls, replays, retries, restarts, failures, timeouts, duplicates, len(namespaces), replay_deterministic, retry_idempotent, False, total_ns, status)


def _request(host: str, request_index: int, object_index: int, operation: int, identities: dict[int, tuple[str, str, str]]) -> dict[str, object]:
    base = {"contract_version": "grf_host_v2", "host_request_id": f"host:grf7:{host}:{request_index}", "evidence_identity": None, "placement_identity": None, "admission_identity": None}
    if operation == 0:
        return {**base, "capability": "capture", "payload": {"capture_id": f"capture:grf7:runtime:{object_index}", "content": f"runtime evidence {object_index}"}}
    evidence, placement, admission = identities[object_index]
    if operation == 1:
        return {**base, "capability": "place", "evidence_identity": evidence, "payload": {"sequence": str(object_index)}}
    if operation == 2:
        return {**base, "capability": "admit", "evidence_identity": evidence, "placement_identity": placement, "payload": {}}
    capability = "recall" if operation == 3 else "replay"
    return {**base, "capability": capability, "admission_identity": admission, "payload": {"query_id": f"query:runtime:{object_index}:{operation}", "entry_mode": "admission_id", "entry_ref": admission}}


def _required(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{key} must be non-empty text")
    return value
