"""Configuration-only adapter wrapper for declarative GRF host skeletons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .grf_file_adapter import GRFFileAdapter


class GRFDeclaredHostAdapter:
    def __init__(self, workspace: Path, declaration_path: Path) -> None:
        payload = json.loads(Path(declaration_path).read_text(encoding="utf-8"))
        if payload.get("contract_version") != "grf_host_v1" or payload.get("mode") != "declarative_skeleton" or not isinstance(payload.get("capabilities"), list):
            raise ValueError("invalid GRF host declaration")
        self._capabilities = frozenset(payload["capabilities"])
        self._file_adapter = GRFFileAdapter(workspace)

    def handle_mapping(self, payload: dict[str, Any]) -> dict[str, object]:
        if payload.get("capability") not in self._capabilities:
            return {"contract_version": "grf_host_v1", "ok": False, "error_code": "unsupported_declared_capability"}
        return self._file_adapter.handle_mapping(payload)
