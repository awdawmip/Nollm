"""Incremental real-source capture over the existing GRF file facade."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .capture import GRFCaptureRequest
from .facade import GRFFacade
from .real_sources import FileSourceConnector, SourceDocument, connector_for


@dataclass(frozen=True)
class IngestionResult:
    source_id: str
    revision: str
    created_shards: tuple[str, ...]
    unchanged: bool
    retired: bool = False


class IncrementalIngestion:
    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace)
        self.facade = GRFFacade(workspace)
        self.connector = FileSourceConnector()
        self.index_path = self.workspace / "grfs" / "manifests" / "grf8_source_index.json"

    def ingest_file(self, path: Path, recorded_at: str) -> IngestionResult:
        document = self.connector.load(path, recorded_at)
        connector = connector_for(document.source_type)
        index = self._load()
        prior = index.get(document.source_id)
        if prior and prior["revision"] == document.revision and not prior["retired"]:
            return IngestionResult(document.source_id, document.revision, (), True)
        shards = []
        for window in connector.windows(document):
            request = GRFCaptureRequest(f"{document.source_id}:{document.revision}:{window.ordinal}", window.content, "imported_text", (window.window_id,), recorded_at, "grf8_file_source")
            receipt = self.facade.capture(request)
            if receipt.status == "captured" and receipt.shard_id:
                shards.append(receipt.shard_id)
        index[document.source_id] = {"source_path": document.source_path, "source_type": document.source_type, "revision": document.revision, "window_ids": [window.window_id for window in connector.windows(document)], "shard_ids": shards, "retired": False}
        self._save(index)
        return IngestionResult(document.source_id, document.revision, tuple(shards), False)

    def retire(self, source_id: str) -> IngestionResult:
        index = self._load()
        if source_id not in index:
            raise FileNotFoundError(source_id)
        entry = index[source_id]
        entry["retired"] = True
        self._save(index)
        return IngestionResult(source_id, str(entry["revision"]), (), False, True)

    def _load(self) -> dict[str, dict[str, object]]:
        return json.loads(self.index_path.read_text(encoding="utf-8")) if self.index_path.exists() else {}

    def _save(self, index: dict[str, dict[str, object]]) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(index, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
