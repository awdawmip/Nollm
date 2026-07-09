"""Path-safe GRF object file naming."""

from __future__ import annotations

from hashlib import sha256


def safe_object_path(object_type: str, object_id: str) -> str:
    """Return a stable filename that never exposes protocol object ids."""

    _require_component(object_type, "object_type")
    _require_component(object_id, "object_id")
    digest = sha256(f"{object_type}\0{object_id}".encode("utf-8")).hexdigest()
    return f"{digest}.json"


def _require_component(value: str, label: str) -> None:
    if not isinstance(value, str) or value == "" or "\0" in value:
        raise ValueError(f"{label} must be non-empty text without NUL")
