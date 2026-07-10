"""Incremental exact-window ingestion without whole-file rebuilds."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .capture import GRFCaptureRequest
from .facade import GRFFacade
from .real_sources import FileSourceConnector, SourceWindow, connector_for
from .source_window import SourceWindowRecord


@dataclass(frozen=True)
class IngestionResult:
    source_id: str
    revision: str
    created_shards: tuple[str, ...]
    unchanged: bool
    retired: bool = False
    reused_shards: tuple[str, ...] = ()
    retired_shards: tuple[str, ...] = ()


class IncrementalIngestion:
    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace)
        self.facade = GRFFacade(workspace)
        self.connector = FileSourceConnector()
        self.index_path = self.workspace / "grfs" / "manifests" / "source_index.json"

    def ingest_file(self, path: Path, recorded_at: str) -> IngestionResult:
        document = self.connector.load(path, recorded_at)
        windows = connector_for(document.source_type).windows(document)
        index = self._load()
        prior = index.get(document.source_id, {})
        prior_windows = {str(item["window_id"]): item for item in prior.get("windows", [])}
        created, reused = [], []
        current = []
        for window in windows:
            previous = prior_windows.pop(window.window_id, None)
            if previous is not None and previous.get("fingerprint") == window.fingerprint and not previous.get("retired", False):
                reused.append(str(previous["shard_id"]))
                current.append({**previous, **_window_mapping(window), "retired": False})
                continue
            self.facade.store.write_source_window(SourceWindowRecord(
                window.window_id, "file", (window.source_id,), window.recorded_at,
                policy_ref="exact_source_window_v1", source_id=window.source_id,
                source_path=window.source_path, source_type=window.source_type,
                encoding=window.encoding, newline_style=window.newline_style,
                start_offset=window.start_offset, end_offset=window.end_offset,
                ordinal=window.ordinal, exact_content=window.content,
            ), recorded_at)
            request = GRFCaptureRequest(
                f"{document.source_id}:{window.window_id}:{window.fingerprint}", window.content,
                "imported_text", (window.window_id,), recorded_at, "grf_file_source",
            )
            receipt = self.facade.capture(request)
            if receipt.status != "captured" or receipt.shard_id is None:
                raise ValueError(f"capture failed for {window.window_id}: {receipt.error}")
            created.append(receipt.shard_id)
            current.append({**_window_mapping(window), "fingerprint": window.fingerprint, "shard_id": receipt.shard_id, "retired": False})
        retired_shards = tuple(str(item["shard_id"]) for item in prior_windows.values() if not item.get("retired", False))
        index[document.source_id] = {
            "source_path": document.source_path, "source_type": document.source_type,
            "encoding": document.encoding, "newline_style": document.newline_style,
            "revision": document.revision, "retired": False, "windows": current,
            "retired_shards": retired_shards,
        }
        self._save(index)
        return IngestionResult(document.source_id, document.revision, tuple(created), not created and not retired_shards, False, tuple(reused), retired_shards)

    def retire(self, source_id: str) -> IngestionResult:
        index = self._load()
        if source_id not in index:
            raise FileNotFoundError(source_id)
        entry = index[source_id]
        entry["retired"] = True
        retired = tuple(str(item["shard_id"]) for item in entry.get("windows", ()) if not item.get("retired", False))
        self._save(index)
        return IngestionResult(source_id, str(entry["revision"]), (), False, True, (), retired)

    def _load(self) -> dict[str, dict[str, object]]:
        return json.loads(self.index_path.read_text(encoding="utf-8")) if self.index_path.exists() else {}

    def _save(self, index: dict[str, dict[str, object]]) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(index, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")


def _window_mapping(window: SourceWindow) -> dict[str, object]:
    return {
        "window_id": window.window_id, "ordinal": window.ordinal,
        "start_offset": window.start_offset, "end_offset": window.end_offset,
        "exact_content": window.content, "encoding": window.encoding,
        "newline_style": window.newline_style,
    }
