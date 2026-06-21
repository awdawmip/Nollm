from __future__ import annotations

from .archive_manifest import sha256_bytes


NORMALIZATION_ID = "nollm.legacy_text_normalization.v1"


def normalize_legacy_text(raw: bytes) -> str:
    text = raw.decode("utf-8")
    return " ".join(text.split())


def text_hash(text: str) -> str:
    return "sha256:" + sha256_bytes(text.encode("utf-8"))


def source_range_hash(raw: bytes) -> str:
    return "sha256:" + sha256_bytes(raw)
