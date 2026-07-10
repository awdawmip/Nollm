from nollm.grf.real_sources import FileSourceConnector, connector_for
from nollm.grf.ingestion import IncrementalIngestion
from nollm.grf.facade import GRFFacade


def _decision(name: str, q: int) -> dict[str, object]:
    return {
        "action": "place", "decision_id": f"decision:{name}",
        "candidate_id": f"candidate:{name}", "placement_id": f"placement:{name}",
        "decided_by": "human", "selected_cell": {
            "profile_id": "eisenstein_exact_v1", "chart_id": "chart:explicit",
            "layer": 0, "q": q, "r": 0,
        },
    }


def test_file_connector_preserves_original_meaningful_units(tmp_path) -> None:
    path = tmp_path / "notes.md"
    path.write_bytes(b"# Title\nfirst\n\n## Next\nsecond")
    document = FileSourceConnector().load(path, "2026-07-10T00:00:00Z")
    windows = FileSourceConnector().windows(document)
    assert document.source_type == "markdown"
    assert tuple(item.content for item in windows) == ("# Title\nfirst\n\n", "## Next\nsecond")
    assert all(item.content == document.content[item.start_offset:item.end_offset] for item in windows)


def test_exact_windows_preserve_json_bom_crlf_and_code_tokens(tmp_path) -> None:
    json_path = tmp_path / "facts.json"
    json_content = '\ufeff{\r\n  "z": 9007199254740993,\r\n  "name": "Ming\u2603"\r\n}\r\n'
    json_path.write_bytes(json_content.encode("utf-8"))
    json_document = FileSourceConnector().load(json_path, "2026-07-11T00:00:00Z")
    assert json_document.newline_style == "crlf"
    assert FileSourceConnector().windows(json_document)[0].content == json_content
    code_path = tmp_path / "module.py"
    code_content = "# heading\n@decorator\ndef first():\n    return 1\n\nclass Second:\n    pass\n"
    code_path.write_bytes(code_content.encode("utf-8"))
    code_document = FileSourceConnector().load(code_path, "2026-07-11T00:00:00Z")
    assert "def first" in "".join(item.content for item in FileSourceConnector().windows(code_document))
    assert "class Second" in "".join(item.content for item in FileSourceConnector().windows(code_document))


def test_six_explicit_source_connectors_are_selectable() -> None:
    assert {type(connector_for(kind)).__name__ for kind in ("markdown", "text", "json", "jsonl", "code", "chat_log")} == {"MarkdownSource", "TextSource", "JsonSource", "JsonlSource", "CodeSource", "ChatLogSource"}


def test_incremental_ingestion_is_idempotent_and_retirement_is_source_scoped(tmp_path) -> None:
    first, second = tmp_path / "first.txt", tmp_path / "second.txt"
    first.write_text("first evidence", encoding="utf-8")
    second.write_text("second evidence", encoding="utf-8")
    ingestion = IncrementalIngestion(tmp_path / "workspace")
    one = ingestion.ingest_file(first, "2026-07-10T00:00:00Z")
    two = ingestion.ingest_file(second, "2026-07-10T00:00:00Z")
    assert ingestion.ingest_file(first, "2026-07-10T00:00:01Z").unchanged
    assert ingestion.retire(one.source_id).retired
    assert two.created_shards


def test_incremental_window_change_preserves_unmodified_shards(tmp_path) -> None:
    path = tmp_path / "facts.jsonl"
    path.write_text('{"id":1}\n{"id":2}\n{"id":3}\n', encoding="utf-8")
    ingestion = IncrementalIngestion(tmp_path / "workspace")
    first = ingestion.ingest_file(path, "2026-07-11T00:00:00Z")
    path.write_text('{"id":1}\n{"id":20}\n{"id":3}\n', encoding="utf-8")
    second = ingestion.ingest_file(path, "2026-07-11T00:00:01Z")
    assert len(first.created_shards) == 3
    assert len(second.created_shards) == 1
    assert {first.created_shards[0], first.created_shards[2]} == set(second.reused_shards)
    manifest = (tmp_path / "workspace" / "grfs" / "manifests" / "source_index.json").read_text(encoding="utf-8")
    assert '"start_offset"' in manifest and '"exact_content"' in manifest


def test_facade_exposes_file_first_capture_source(tmp_path) -> None:
    path = tmp_path / "data.jsonl"
    path.write_text('{"fact":"one"}\n{"fact":"two"}\n', encoding="utf-8")
    result = GRFFacade(tmp_path / "workspace").capture_source(path, "2026-07-10T00:00:00Z")
    assert len(result.created_shards) == 2
    assert GRFFacade(tmp_path / "workspace").get_source(result.created_shards[0]) == path.read_bytes().decode("utf-8").splitlines(keepends=True)[0]


def test_facade_retire_preserves_captured_source(tmp_path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("retained after retirement", encoding="utf-8")
    facade = GRFFacade(tmp_path / "workspace")
    result = facade.capture_source(path, "2026-07-10T00:00:00Z")
    assert facade.retire(result.source_id).retired
    assert facade.get_source(result.created_shards[0]) == "retained after retirement"


def test_facade_text_snapshot_and_restore_are_file_first(tmp_path) -> None:
    facade = GRFFacade(tmp_path / "workspace")
    receipt = facade.capture_text("capture:text", "retained", "window:text", "2026-07-11T00:00:00Z")
    restored = GRFFacade.restore(facade.snapshot(tmp_path / "snapshot"), tmp_path / "restored")
    assert restored.get_source(receipt.shard_id) == "retained"


def test_batch_place_then_admit_keeps_distinct_identities(tmp_path) -> None:
    path = tmp_path / "facts.jsonl"
    path.write_text('{"fact":"one"}\n{"fact":"two"}\n', encoding="utf-8")
    facade = GRFFacade(tmp_path / "workspace")
    ingested = facade.capture_source(path, "2026-07-10T00:00:00Z")
    placed = tuple(facade.place(shard, "window:batch", _decision(f"batch:{index}", index), "2026-07-10T00:00:01Z") for index, shard in enumerate(ingested.created_shards))
    assert all(item.admission_record is None and item.placement_record is not None for item in placed)
    admitted = facade.admit_batch(tuple((item.placement_record.shard_id, item.placement_record.placement_id) for item in placed), "2026-07-10T00:00:02Z", "batch_explicit")
    assert len({item.admission_id for item in admitted}) == 2


def test_replacement_creates_new_placement_without_losing_source(tmp_path) -> None:
    facade = GRFFacade(tmp_path / "workspace")
    shard = facade.capture_text("capture:replace", "retained replacement source", "window:replace", "2026-07-11T00:00:00Z").shard_id
    original = facade.place(shard, "window:replace", _decision("replace:original", 0), "2026-07-11T00:00:01Z").placement_record
    replacement = facade.place(shard, "window:replace", _decision("replace:changed", 1), "2026-07-11T00:00:02Z").placement_record
    assert original.placement_id != replacement.placement_id
    assert facade.get_source(shard) == "retained replacement source"
