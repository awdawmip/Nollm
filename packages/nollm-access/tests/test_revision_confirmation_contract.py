import pytest

from nollm_access import RevisionConfirmationResult


def mapping(**changes: object) -> dict[str, object]:
    value = {
        "schema_version": "nollm_openclaw_revision_confirmation_v1",
        "provisional_id": "revision:abc",
        "outcome": "confirm_revision",
        "relation": "same_subject_same_slot_supersedes",
    }
    value.update(changes)
    return value


def test_confirmation_requires_exact_wire_and_all_semantic_conditions() -> None:
    result = RevisionConfirmationResult.from_mapping(mapping())
    assert result.confirmed is True
    assert result.to_mapping() == mapping()
    with pytest.raises(ValueError, match="disagree"):
        RevisionConfirmationResult.from_mapping(mapping(relation="different_subject_or_non_superseding"))
    with pytest.raises(ValueError, match="envelope"):
        RevisionConfirmationResult.from_mapping({**mapping(), "extra": True})


def test_reject_and_defer_are_structural_results_not_python_semantic_decisions() -> None:
    rejected = RevisionConfirmationResult.from_mapping(mapping(
        outcome="reject_revision",
        relation="different_subject_or_non_superseding",
    ))
    deferred = RevisionConfirmationResult.from_mapping(mapping(
        outcome="defer",
        relation="uncertain",
    ))
    assert rejected.confirmed is False
    assert deferred.confirmed is False


def test_model_wire_has_only_contract_fields_and_host_binds_provisional() -> None:
    wire = {
        "schema_version": "nollm_openclaw_revision_confirmation_v1",
        "outcome": "confirm_revision",
        "relation": "same_subject_same_slot_supersedes",
    }
    result = RevisionConfirmationResult.from_wire_mapping(wire, "revision:abc")
    assert result.to_mapping() == mapping()
    with pytest.raises(ValueError, match="wire envelope"):
        RevisionConfirmationResult.from_wire_mapping({**wire, "reason_text": "not allowed"}, "revision:abc")
