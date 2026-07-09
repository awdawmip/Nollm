from __future__ import annotations

from nollm.grf.importers import import_oca_like_capture


def test_oca_like_capture_import_does_not_use_message_id_as_shard_id() -> None:
    result = import_oca_like_capture(
        {
            "request_id": "oca-request-1",
            "capture_id": "capture:oca:1",
            "content": "oca explicit capture",
            "origin_reference": "openclaw-message-42",
            "context_reference": "source:oca:ctx",
            "recorded_at": "2026-07-09T00:00:00Z",
            "role_label": "assistant",
        }
    )

    assert result.capture_request.capture_id == "capture:oca:1"
    assert result.capture_request.origin_kind == "assistant_output"
    assert result.capture_request.source_window_refs == ("source:oca:ctx",)
    assert result.source_window.refs == ("openclaw-message-42", "source:oca:ctx")
    assert "openclaw-message-42" not in result.capture_request.capture_id
