"""DE1 file-first Memory Substrate store."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from nollm.dream_geometry.protocol.contracts import (
    InterpretationAuthoringMode,
    InterpretationKind,
    LedgerEventKind,
    OriginKind,
    RevisionRelation,
    UsageState,
)

from .types import (
    FORMAT_VERSION,
    DreamShard,
    InterpretationRecord,
    LedgerEvent,
    OriginDescriptor,
    RevisionEdge,
    RevisionThread,
    TemporalContext,
    UsageStateTransition,
    canonical_json,
    canonical_payload,
    payload_key,
)


@dataclass(frozen=True)
class WriteResult:
    record_id: str
    created: bool
    idempotent: bool
    ledger_event_id: str | None


class MemorySubstrateStore:
    """Single-process, single-writer, file-first DE1 store."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self._paths = {
            "shards": self.root / "shards",
            "interpretations": self.root / "interpretations",
            "revision_threads": self.root / "revision_threads",
            "state_transitions": self.root / "state_transitions",
            "ledger": self.root / "ledger",
        }
        self.root.mkdir(parents=True, exist_ok=True)
        for path in self._paths.values():
            path.mkdir(parents=True, exist_ok=True)
        self._format_path = self.root / "format.json"
        self._ledger_path = self._paths["ledger"] / "events.jsonl"
        self._ensure_format()
        self._ledger_path.touch(exist_ok=True)
        self._validate_store()

    def put_dream_shard(self, shard: DreamShard) -> WriteResult:
        return self._put_record("shards", shard.shard_id, shard, LedgerEventKind.shard_recorded)

    def put_interpretation(self, record: InterpretationRecord) -> WriteResult:
        if not self._record_exists(record.subject_shard_id):
            raise ValueError("interpretation subject shard missing")
        return self._put_record("interpretations", record.interpretation_id, record, LedgerEventKind.interpretation_recorded)

    def put_revision_thread(self, thread: RevisionThread) -> WriteResult:
        for member in thread.member_record_ids:
            if not self._record_exists(member):
                raise ValueError("revision member missing")
        return self._put_record("revision_threads", thread.thread_id, thread, LedgerEventKind.revision_thread_recorded)

    def record_usage_transition(self, transition: UsageStateTransition) -> WriteResult:
        if not self._record_exists(transition.target_record_id):
            raise ValueError("usage transition target missing")
        current = self.get_usage_state(transition.target_record_id)
        if transition.expected_from_state is not None and current is not transition.expected_from_state:
            raise ValueError("expected_from_state mismatch")
        if current is transition.to_state:
            raise ValueError("usage state transition must change state")
        return self._put_record("state_transitions", transition.transition_id, transition, LedgerEventKind.usage_state_transition_recorded)

    def get_dream_shard(self, shard_id: str) -> DreamShard:
        return _dream_shard_from_payload(self._read_record("shards", shard_id, "dream_shard"))

    def get_interpretation(self, interpretation_id: str) -> InterpretationRecord:
        return _interpretation_from_payload(self._read_record("interpretations", interpretation_id, "interpretation_record"))

    def get_revision_thread(self, thread_id: str) -> RevisionThread:
        return _revision_thread_from_payload(self._read_record("revision_threads", thread_id, "revision_thread"))

    def get_usage_state(self, record_id: str) -> UsageState:
        projection = self.state_projection()
        if record_id not in projection:
            raise ValueError("usage state target missing")
        return projection[record_id]

    def read_ledger(self) -> tuple[LedgerEvent, ...]:
        events = []
        for line in self._ledger_path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            events.append(_ledger_event_from_payload(json.loads(line)))
        return tuple(events)

    def state_projection(self) -> dict[str, UsageState]:
        projection: dict[str, UsageState] = {}
        for shard in self._load_all("shards", _dream_shard_from_payload, "dream_shard"):
            projection[shard.shard_id] = shard.initial_usage_state
        for interpretation in self._load_all("interpretations", _interpretation_from_payload, "interpretation_record"):
            projection[interpretation.interpretation_id] = interpretation.initial_usage_state
        for event in self.read_ledger():
            if event.event_kind is not LedgerEventKind.usage_state_transition_recorded:
                continue
            transition = self._load_transition(event.record_id)
            current = projection.get(transition.target_record_id)
            if current is None:
                raise ValueError("usage transition target missing")
            if transition.expected_from_state is not None and current is not transition.expected_from_state:
                raise ValueError("expected_from_state mismatch")
            if current is transition.to_state:
                raise ValueError("usage state transition must change state")
            projection[transition.target_record_id] = transition.to_state
        return projection

    def _put_record(self, bucket: str, record_id: str, record: object, event_kind: LedgerEventKind) -> WriteResult:
        path = self._record_path(bucket, record_id)
        rendered = canonical_json(record)
        key = payload_key(record)
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if existing == rendered:
                return WriteResult(record_id, False, True, None)
            raise ValueError("same record_id different payload")
        _atomic_write_text(path, rendered)
        event = self._make_event(event_kind, record_id, key, _record_recorded_at(record))
        with self._ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical_json(event) + "\n")
        return WriteResult(record_id, True, False, event.event_id)

    def _make_event(self, event_kind: LedgerEventKind, record_id: str, key: str, recorded_at: str | None) -> LedgerEvent:
        ordinal = len(self.read_ledger())
        event_payload = {"kind": event_kind.value, "record_id": record_id, "payload_key": key, "ordinal": ordinal}
        event_id = "ledger:" + sha256(json.dumps(event_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:32]
        return LedgerEvent(event_id, ordinal, event_kind, record_id, key, recorded_at)

    def _record_path(self, bucket: str, record_id: str) -> Path:
        name = sha256(record_id.encode("utf-8")).hexdigest() + ".json"
        path = self._paths[bucket] / name
        if self._paths[bucket] not in path.parents:
            raise ValueError("record path escapes root")
        return path

    def _read_record(self, bucket: str, record_id: str, record_type: str) -> dict:
        path = self._record_path(bucket, record_id)
        if not path.exists():
            raise ValueError("record missing")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("record_type") != record_type:
            raise ValueError("record type mismatch")
        return payload

    def _load_transition(self, transition_id: str) -> UsageStateTransition:
        return _transition_from_payload(self._read_record("state_transitions", transition_id, "usage_state_transition"))

    def _load_all(self, bucket: str, loader, record_type: str) -> tuple:
        records = []
        for path in sorted(self._paths[bucket].glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("record_type") != record_type:
                raise ValueError("record type mismatch")
            records.append(loader(payload))
        return tuple(records)

    def _record_exists(self, record_id: str) -> bool:
        return self._record_path("shards", record_id).exists() or self._record_path("interpretations", record_id).exists()

    def _ensure_format(self) -> None:
        payload = {"format_version": FORMAT_VERSION, "store_kind": "memory_substrate"}
        if self._format_path.exists():
            existing = json.loads(self._format_path.read_text(encoding="utf-8"))
            if existing != payload:
                raise ValueError("unsupported format version")
            return
        _atomic_write_text(self._format_path, json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True))

    def _validate_store(self) -> None:
        for interpretation in self._load_all("interpretations", _interpretation_from_payload, "interpretation_record"):
            if not self._record_path("shards", interpretation.subject_shard_id).exists():
                raise ValueError("interpretation subject shard missing")
        for thread in self._load_all("revision_threads", _revision_thread_from_payload, "revision_thread"):
            for member in thread.member_record_ids:
                if not self._record_exists(member):
                    raise ValueError("revision member missing")
        events = self.read_ledger()
        for expected, event in enumerate(events):
            if event.ordinal != expected:
                raise ValueError("ledger ordinal mismatch")
            bucket, record_type = _bucket_for_event(event.event_kind)
            payload = self._read_record(bucket, event.record_id, record_type)
            record = _record_from_payload(record_type, payload)
            if payload_key(record) != event.payload_key:
                raise ValueError("ledger payload_key mismatch")
        self.state_projection()


def open_store(root: Path) -> MemorySubstrateStore:
    return MemorySubstrateStore(root)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _record_recorded_at(record: object) -> str | None:
    if isinstance(record, UsageStateTransition):
        return record.recorded_at
    if isinstance(record, DreamShard):
        return record.temporal_context.captured_at
    return None


def _bucket_for_event(event_kind: LedgerEventKind) -> tuple[str, str]:
    if event_kind is LedgerEventKind.shard_recorded:
        return "shards", "dream_shard"
    if event_kind is LedgerEventKind.interpretation_recorded:
        return "interpretations", "interpretation_record"
    if event_kind is LedgerEventKind.revision_thread_recorded:
        return "revision_threads", "revision_thread"
    if event_kind is LedgerEventKind.usage_state_transition_recorded:
        return "state_transitions", "usage_state_transition"
    raise ValueError("unsupported ledger event kind")


def _record_from_payload(record_type: str, payload: dict) -> object:
    if record_type == "dream_shard":
        return _dream_shard_from_payload(payload)
    if record_type == "interpretation_record":
        return _interpretation_from_payload(payload)
    if record_type == "revision_thread":
        return _revision_thread_from_payload(payload)
    if record_type == "usage_state_transition":
        return _transition_from_payload(payload)
    raise ValueError("unsupported record type")


def _origin_from_payload(payload: dict) -> OriginDescriptor:
    return OriginDescriptor(OriginKind(payload["kind"]), payload["reference"], payload["context_reference"], payload["role_label"])


def _temporal_from_payload(payload: dict) -> TemporalContext:
    return TemporalContext(payload["captured_at"], payload["source_time_expression"], payload["reference_instant"], payload["locale_hint"])


def _dream_shard_from_payload(payload: dict) -> DreamShard:
    return DreamShard(
        payload["shard_id"],
        payload["content"],
        _origin_from_payload(payload["origin"]),
        _temporal_from_payload(payload["temporal_context"]),
        tuple(payload["context_refs"]),
        UsageState(payload["initial_usage_state"]),
        payload["format_version"],
    )


def _interpretation_from_payload(payload: dict) -> InterpretationRecord:
    return InterpretationRecord(
        payload["interpretation_id"],
        payload["subject_shard_id"],
        InterpretationKind(payload["kind"]),
        payload["statement"],
        InterpretationAuthoringMode(payload["authoring_mode"]),
        tuple(payload["basis_refs"]),
        tuple(payload["context_refs"]),
        UsageState(payload["initial_usage_state"]),
        payload["format_version"],
    )


def _edge_from_payload(payload: dict) -> RevisionEdge:
    return RevisionEdge(payload["from_record_id"], payload["to_record_id"], RevisionRelation(payload["relation"]), tuple(payload["basis_refs"]))


def _revision_thread_from_payload(payload: dict) -> RevisionThread:
    return RevisionThread(
        payload["thread_id"],
        tuple(payload["member_record_ids"]),
        tuple(_edge_from_payload(edge) for edge in payload["edges"]),
        tuple(payload["context_refs"]),
        payload["format_version"],
    )


def _transition_from_payload(payload: dict) -> UsageStateTransition:
    expected = UsageState(payload["expected_from_state"]) if payload["expected_from_state"] is not None else None
    return UsageStateTransition(
        payload["transition_id"],
        payload["target_record_id"],
        expected,
        UsageState(payload["to_state"]),
        tuple(payload["reason_refs"]),
        payload["recorded_at"],
        payload["format_version"],
    )


def _ledger_event_from_payload(payload: dict) -> LedgerEvent:
    return LedgerEvent(
        payload["event_id"],
        payload["ordinal"],
        LedgerEventKind(payload["event_kind"]),
        payload["record_id"],
        payload["payload_key"],
        payload["recorded_at"],
    )


__all__ = ["MemorySubstrateStore", "WriteResult", "open_store"]
