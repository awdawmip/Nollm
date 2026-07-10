from nollm.grf.real_sources import FileSourceConnector
from nollm.grf.ingestion import IncrementalIngestion
from nollm.grf.facade import GRFFacade


def test_file_connector_preserves_original_meaningful_units(tmp_path) -> None:
    path = tmp_path / "notes.md"
    path.write_text("# Title\nfirst\n\n## Next\nsecond", encoding="utf-8")
    document = FileSourceConnector().load(path, "2026-07-10T00:00:00Z")
    windows = FileSourceConnector().windows(document)
    assert document.source_type == "markdown"
    assert tuple(item.content for item in windows) == ("# Title\nfirst", "Next\nsecond")


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


def test_facade_exposes_file_first_capture_source(tmp_path) -> None:
    path = tmp_path / "data.jsonl"
    path.write_text('{"fact":"one"}\n{"fact":"two"}\n', encoding="utf-8")
    result = GRFFacade(tmp_path / "workspace").capture_source(path, "2026-07-10T00:00:00Z")
    assert len(result.created_shards) == 2
    assert GRFFacade(tmp_path / "workspace").get_source(result.created_shards[0]) == '{"fact":"one"}'


def test_batch_place_then_admit_keeps_distinct_identities(tmp_path) -> None:
    path = tmp_path / "facts.jsonl"
    path.write_text('{"fact":"one"}\n{"fact":"two"}\n', encoding="utf-8")
    facade = GRFFacade(tmp_path / "workspace")
    ingested = facade.capture_source(path, "2026-07-10T00:00:00Z")
    placed = facade.place_batch(ingested.created_shards, "window:batch", {"policy_id": "grf_deterministic_policy_v1"}, "2026-07-10T00:00:01Z")
    assert all(item.admission_record is None and item.placement_record is not None for item in placed)
    admitted = facade.admit_batch(tuple((item.placement_record.shard_id, item.placement_record.placement_id) for item in placed), "2026-07-10T00:00:02Z", "batch_explicit")
    assert len({item.admission_id for item in admitted}) == 2
