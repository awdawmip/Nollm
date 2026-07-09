from __future__ import annotations

from nollm.grf.source_window import SourceWindowRecord
from nollm.grf.storage import GRFFileStore


def test_source_window_persists_protocol_id_with_hash_filename(tmp_path) -> None:
    store = GRFFileStore(tmp_path)
    window = SourceWindowRecord("source:window:task/unsafe?", "validation_fixture", ("fixture:alpha",), "2026-07-09T00:00:00Z", policy_ref="policy:fixture")
    path = store.write_source_window(window, "2026-07-09T00:00:01Z")

    assert "source:window" not in path.name
    assert "/" not in path.name
    assert store.read_source_window(window.window_id) == window
