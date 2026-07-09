"""Append-only GRF ledger."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from .json_canonical import canonical_dumps, canonical_loads

LEDGER_EVENT_TYPES = frozenset(
    {
        "object_written",
        "object_reopened_same_bytes",
        "object_write_rejected_different_bytes",
        "relation_field_rebuilt",
        "recall_digest_written",
        "stitch_rejected_recorded",
    }
)


@dataclass(frozen=True)
class GRFLedgerEvent:
    event_id: str
    event_type: str
    object_type: str
    object_id: str
    object_path: str
    object_sha256: str
    recorded_at: str
    previous_event_id: str | None = None

    def __post_init__(self) -> None:
        if self.event_type not in LEDGER_EVENT_TYPES:
            raise ValueError("unknown ledger event type")

    def to_mapping(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "object_path": self.object_path,
            "object_sha256": self.object_sha256,
            "recorded_at": self.recorded_at,
            "previous_event_id": self.previous_event_id,
        }


class GRFLedger:
    def __init__(self, root: Path) -> None:
        self.path = Path(root) / "grfs" / "ledger.jsonl"

    def append(self, event_type: str, object_type: str, object_id: str, object_path: Path, object_sha256: str, recorded_at: str) -> GRFLedgerEvent:
        previous = self.last_event_id()
        material = f"{previous}|{event_type}|{object_type}|{object_id}|{object_path.as_posix()}|{object_sha256}|{recorded_at}"
        event = GRFLedgerEvent("grfl_" + sha256(material.encode("utf-8")).hexdigest()[:32], event_type, object_type, object_id, object_path.as_posix(), object_sha256, recorded_at, previous)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab") as handle:
            handle.write(canonical_dumps(event.to_mapping()))
        return event

    def events(self) -> tuple[GRFLedgerEvent, ...]:
        if not self.path.exists():
            return ()
        out = []
        for line in self.path.read_bytes().splitlines():
            payload = canonical_loads(line + b"\n")
            out.append(GRFLedgerEvent(payload["event_id"], payload["event_type"], payload["object_type"], payload["object_id"], payload["object_path"], payload["object_sha256"], payload["recorded_at"], payload["previous_event_id"]))
        return tuple(out)

    def last_event_id(self) -> str | None:
        events = self.events()
        return None if not events else events[-1].event_id
