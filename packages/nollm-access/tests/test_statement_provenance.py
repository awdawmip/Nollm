from hashlib import sha256

import pytest

from nollm_access import (
    ExactEvidenceSpan,
    FileStatementProvenanceStore,
    ResolvedReferenceProvenance,
    StatementProvenance,
)
from nollm_access.provenance import (
    LEGACY_PROVENANCE_SCHEMA_VERSION,
    PROVENANCE_SCHEMA_VERSION,
)


def provenance(
    statement_id: str = "dream:one", content: str = "Tokyo rain"
) -> StatementProvenance:
    span = ExactEvidenceSpan(
        "e1",
        "capture-one",
        "user",
        0,
        5,
        "Tokyo",
        sha256(b"Tokyo").hexdigest(),
        "1" * 64,
    )
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
    span = ExactEvidenceSpan(
        "e1",
        "capture-one",
        "user",
        0,
        5,
        "Tokyo",
        sha256(b"Tokyo").hexdigest(),
        "1" * 64,
    )
    bad_reference = ResolvedReferenceProvenance(
        "r1", "location", "Tokyo", ("missing",), ()
    )
    with pytest.raises(ValueError, match="cross-link"):
        StatementProvenance(
            "dream:one",
            "2" * 64,
            ("capture-one",),
            (),
            (span,),
            (bad_reference,),
            "writer",
            "prompt",
            1,
        )
    store = FileStatementProvenanceStore(tmp_path)
    store.put(provenance())
    with pytest.raises(FileExistsError):
        store.put(provenance(content="different"))


def test_revision_provenance_preserves_predecessor_identity():
    value = provenance("dream:new")
    revised = StatementProvenance(
        value.statement_id,
        value.content_sha256,
        value.source_capture_ids,
        value.context_capture_ids,
        value.evidence_spans,
        value.resolved_references,
        value.writer_schema_version,
        value.writer_prompt_version,
        value.created_at_epoch_ms,
        "dream:old",
        "exact",
    )
    assert revised.revision_predecessor_statement_id == "dream:old"


def test_v2_provenance_reopens_origin_and_derived_lineage(tmp_path):
    base = provenance("dream:derived")
    value = StatementProvenance(
        base.statement_id,
        base.content_sha256,
        base.source_capture_ids,
        base.context_capture_ids,
        base.evidence_spans,
        base.resolved_references,
        "writer-v4",
        "prompt-v4",
        base.created_at_epoch_ms,
        None,
        "exact",
        ("assistant", "model_inference", "recalled_memory", "tool"),
        ("dream:prior",),
        "evaluation-1",
        3,
        PROVENANCE_SCHEMA_VERSION,
    )
    store = FileStatementProvenanceStore(tmp_path)
    store.put(value)
    reopened = FileStatementProvenanceStore(tmp_path).get(value.statement_id)
    assert reopened == value
    assert reopened.origin_kinds == (
        "assistant",
        "model_inference",
        "recalled_memory",
        "tool",
    )
    assert reopened.derived_from_statement_ids == ("dream:prior",)
    assert reopened.evaluation_id == "evaluation-1"
    assert reopened.continuation_pass == 3


def test_legacy_v1_provenance_reopens_byte_for_byte(tmp_path):
    base = provenance("dream:legacy")
    legacy = StatementProvenance(
        base.statement_id,
        base.content_sha256,
        base.source_capture_ids,
        base.context_capture_ids,
        base.evidence_spans,
        base.resolved_references,
        base.writer_schema_version,
        base.writer_prompt_version,
        base.created_at_epoch_ms,
        None,
        "exact",
        (),
        (),
        None,
        0,
        LEGACY_PROVENANCE_SCHEMA_VERSION,
    )
    digest = sha256(legacy.statement_id.encode("utf-8")).hexdigest()
    path = tmp_path / "access" / "statement-provenance" / digest[:2] / f"{digest}.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(legacy.canonical_bytes())
    reopened = FileStatementProvenanceStore(tmp_path).get(legacy.statement_id)
    assert reopened.schema_version == LEGACY_PROVENANCE_SCHEMA_VERSION
    assert reopened.canonical_bytes() == path.read_bytes()
