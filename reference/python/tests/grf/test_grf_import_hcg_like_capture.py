from __future__ import annotations

from nollm.grf.importers import MIGRATION_BOUNDARY_MODE, import_hcg_like_capture


def test_hcg_like_capture_import_preserves_content_and_provenance_refs() -> None:
    result = import_hcg_like_capture(
        {
            "kind": "nollm_hcg_capture_request",
            "version": "1",
            "request_id": "host-request-1",
            "capture": {
                "capture_id": "capture:hcg:1",
                "content": "hcg imported content",
                "origin": {"kind": "user", "reference": "message:hcg:1", "context_reference": "source:hcg:ctx", "role_label": "user"},
                "recorded_at": "2026-07-09T00:00:00Z",
                "context_refs": ["source:hcg:extra"],
                "requested_visibility_scope": "source_window",
            },
            "ignored_extension": {"not": "placement"},
        }
    )

    assert result.mode == MIGRATION_BOUNDARY_MODE
    assert result.capture_request.capture_id == "capture:hcg:1"
    assert result.capture_request.content == "hcg imported content"
    assert result.capture_request.origin_kind == "user_utterance"
    assert result.capture_request.source_window_refs == ("source:hcg:ctx",)
    assert result.source_window.window_id == "source:hcg:ctx"
    assert "message:hcg:1" in result.source_window.refs
    assert "host-request-1" not in result.capture_request.capture_id
    assert result.ignored_fields == ("ignored_extension",)
