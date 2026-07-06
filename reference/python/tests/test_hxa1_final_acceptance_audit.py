from __future__ import annotations

from hashlib import sha256

from validation.hx1.run_hx1_validation import render_report


def test_hxa1_final_acceptance_report_records_audit_matrix_and_boundaries() -> None:
    receipt = {
        "status": "completed",
        "completed_stages": ["capture", "admission", "assembly", "recall"],
        "admission_receipt_ids": ["adm_hx1_a", "adm_hx1_b"],
        "explicit_assembly_admission_ids": ["adm_hx1_a", "adm_hx1_b"],
        "snapshot_source_admission_ids": ["adm_hx1_a", "adm_hx1_b"],
        "dg6_projection_id": "dg6:hx1:test",
        "recall_public_envelope": {"status": "resolved"},
        "output_fingerprint": "sha256:" + "1" * 64,
        "execution_input_fingerprint": "sha256:" + "2" * 64,
    }

    report = render_report(receipt, ())

    for section in ("HXA1-A", "HXA1-B", "HXA1-C", "HXA1-D", "HXA1-E", "HXA1-F"):
        assert section in report
    assert "[ACCEPTED CANDIDATE] HX1 Trusted Host Staged Execution Bridge" in report
    assert "does not merge HX1 to `main`" in report
    for boundary in ("OpenClaw", "agent", "automatic memory", "global discovery", "semantic search"):
        assert boundary in report
    assert sha256.__name__ == "openssl_sha256" or sha256.__name__ == "sha256"
