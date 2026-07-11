from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json


CORE_SECTIONS = ("schema_version", "geometry_registry", "cells", "bridges")


@dataclass(frozen=True)
class SnapshotDiff:
    equal: bool
    left_sha256: str
    right_sha256: str
    changed_top_level_sections: tuple[str, ...]
    left_size_bytes: int
    right_size_bytes: int

    def to_mapping(self) -> dict[str, object]:
        return {
            "equal": self.equal,
            "left_sha256": self.left_sha256,
            "right_sha256": self.right_sha256,
            "changed_top_level_sections": list(self.changed_top_level_sections),
            "left_size_bytes": self.left_size_bytes,
            "right_size_bytes": self.right_size_bytes,
        }


def structural_diff(left: bytes, right: bytes) -> SnapshotDiff:
    if type(left) is not bytes or type(right) is not bytes:
        raise TypeError("snapshot inputs must be bytes")
    equal = left == right
    changed = () if equal else _changed_sections(left, right)
    return SnapshotDiff(
        equal,
        sha256(left).hexdigest(),
        sha256(right).hexdigest(),
        changed,
        len(left),
        len(right),
    )


def _changed_sections(left: bytes, right: bytes) -> tuple[str, ...]:
    try:
        left_document = json.loads(left.decode("utf-8"))
        right_document = json.loads(right.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ("bytes",)
    if type(left_document) is not dict or type(right_document) is not dict:
        return ("bytes",)
    if not set(CORE_SECTIONS).issubset(left_document) or not set(CORE_SECTIONS).issubset(right_document):
        return ("bytes",)
    return tuple(section for section in CORE_SECTIONS if left_document[section] != right_document[section])
