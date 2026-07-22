from hashlib import sha256

import pytest

from nollm_access import (
    ExactEvidenceSpan,
    FileStatementProvenanceStore,
    ResolvedReferenceProvenance,
    StatementProvenance,
)


def provenance(statement_id: str = "dream:one", content: str = "Tokyo rain") -> StatementProvenance:
    span = ExactEvidenceSpan("e1", "capture-one", "user", 0, 5, "Tokyo", sha256(b"Tokyo").hexdigest(), "1" * 64)
    reference = ResolvedReferenceProvenance("r1", "location", "Tokyo", ("e1",), ())
    return StatementProvenance(
        statement_id,
        sha256(content.encode()).hexdigest(),
        ("capture-one",),
        (),
        (span,),
        (reference,),
        "nollm_openclaw_contextual_proposition_writer_v3",
        "proposition-writer-v3-llm-native-evidence-quotes",
        1,
    )


def test_statement_provenance_is_canonical_idempotent_and_reopenable(tmp_path):
    store = FileStatementProvenanceStore(tmp_path)
    value = provenance()
    store.put(value)
    store.put(value)
    reopened = FileStatementProvenanceStore(tmp_path).get("dream:one")
    assert reopened == value
    assert reopened.digest() == sha256(reopened.canonical_bytes()).hexdigest()


def test_statement_provenance_rejects_mismatched_basis_and_rewrite(tmp_path):
    span = ExactEvidenceSpan("e1", "capture-one", "user", 0, 5, "Tokyo", sha256(b"Tokyo").hexdigest(), "1" * 64)
    bad_reference = ResolvedReferenceProvenance("r1", "location", "Tokyo", ("missing",), ())
    with pytest.raises(ValueError, match="cross-link"):
        StatementProvenance("dream:one", "2" * 64, ("capture-one",), (), (span,), (bad_reference,), "writer", "prompt", 1)
    store = FileStatementProvenanceStore(tmp_path)
    store.put(provenance())
    with pytest.raises(FileExistsError):
        store.put(provenance(content="different"))


def test_revision_provenance_preserves_predecessor_identity():
    value = provenance("dream:new")
    revised = StatementProvenance(
        value.statement_id, value.content_sha256, value.source_capture_ids, value.context_capture_ids,
        value.evidence_spans, value.resolved_references, value.writer_schema_version,
        value.writer_prompt_version, value.created_at_epoch_ms, "dream:old", "exact",
    )
    assert revised.revision_predecessor_statement_id == "dream:old"
