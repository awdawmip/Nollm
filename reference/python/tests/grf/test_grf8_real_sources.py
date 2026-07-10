from nollm.grf.real_sources import FileSourceConnector


def test_file_connector_preserves_original_meaningful_units(tmp_path) -> None:
    path = tmp_path / "notes.md"
    path.write_text("# Title\nfirst\n\n## Next\nsecond", encoding="utf-8")
    document = FileSourceConnector().load(path, "2026-07-10T00:00:00Z")
    windows = FileSourceConnector().windows(document)
    assert document.source_type == "markdown"
    assert tuple(item.content for item in windows) == ("# Title\nfirst", "Next\nsecond")
