import dataclasses
import inspect

from nollm.dream_geometry.protocol import contracts
from nollm.dream_geometry.protocol.contracts import (
    ChartTransformState,
    CoverState,
    DA1_ADMISSION_INVARIANTS,
    DE1_MEMORY_SUBSTRATE_INVARIANTS,
    GrowthBasis,
    INVARIANTS,
    InterpretationAuthoringMode,
    InterpretationKind,
    KernelDirection,
    LedgerEventKind,
    ModuleName,
    OBJECT_OWNERSHIP,
    ObjectKind,
    OriginKind,
    RevisionRelation,
    TraceState,
    UsageState,
)


def enum_values(enum_type):
    return [item.value for item in enum_type]


def test_required_enum_values_are_stable() -> None:
    assert enum_values(GrowthBasis) == [
        "explicit_in_shard",
        "deterministic_projection",
        "backed_by_other_shard",
        "source_backed_rule",
        "provisional_llm_generalization",
        "rejected",
    ]
    assert enum_values(ChartTransformState) == ["proposed", "verified", "requires_review", "rejected", "conflict", "deferred"]
    assert enum_values(TraceState) == ["proposed", "accepted", "suppressed", "superseded", "archived"]
    assert enum_values(CoverState) == ["candidate", "stable", "crystallized", "deprecated", "conflicted"]
    assert enum_values(KernelDirection) == ["fine_to_coarse", "coarse_to_fine"]
    assert enum_values(ModuleName) == ["protocol", "evidence", "geometry", "field", "cortex", "admission", "recall", "adapters", "validation"]
    assert enum_values(ObjectKind) == [
        "dream_shard",
        "interpretation_record",
        "revision_thread",
        "usage_state_transition",
        "growth_proposal",
        "query_probe",
        "local_chart",
        "chart_transform",
        "coverage_kernel",
        "growth_trace",
        "coarse_cover",
        "gravity_snapshot",
        "admission_record",
        "recall_digest",
        "ledger_event",
    ]
    assert enum_values(OriginKind) == ["user_utterance", "assistant_utterance", "tool_observation", "imported_text", "internal_reflection", "system_seed", "unknown"]
    assert enum_values(UsageState) == ["tentative", "active", "retired", "rejected"]
    assert enum_values(InterpretationKind) == ["summary", "classification", "relation", "growth_hint", "constraint", "other"]
    assert enum_values(InterpretationAuthoringMode) == ["user_stated", "llm_proposed", "deterministic_projection", "imported_annotation", "unknown"]
    assert enum_values(RevisionRelation) == ["supersedes", "withdraws", "clarifies", "coexists", "conflicts"]
    assert enum_values(LedgerEventKind) == ["shard_recorded", "interpretation_recorded", "revision_thread_recorded", "usage_state_transition_recorded"]


def test_contract_dataclasses_are_frozen_and_do_not_use_any() -> None:
    for name in ["ObjectOwnership", "DependencyRule", "Invariant"]:
        cls = getattr(contracts, name)
        assert dataclasses.is_dataclass(cls)
        assert cls.__dataclass_params__.frozen
        assert "Any" not in inspect.getsource(cls)


def test_object_ownership_mapping_is_complete() -> None:
    ownership = {item.object_kind: item for item in OBJECT_OWNERSHIP}
    assert ownership[ObjectKind.dream_shard].owner is ModuleName.evidence
    assert ownership[ObjectKind.interpretation_record].owner is ModuleName.evidence
    assert ownership[ObjectKind.revision_thread].owner is ModuleName.evidence
    assert ownership[ObjectKind.usage_state_transition].owner is ModuleName.evidence
    assert ownership[ObjectKind.ledger_event].owner is ModuleName.evidence
    assert ownership[ObjectKind.growth_proposal].owner is ModuleName.cortex
    assert ownership[ObjectKind.query_probe].owner is ModuleName.cortex
    assert ownership[ObjectKind.local_chart].owner is ModuleName.geometry
    assert ownership[ObjectKind.chart_transform].owner is ModuleName.geometry
    assert ownership[ObjectKind.coverage_kernel].owner is ModuleName.geometry
    assert ownership[ObjectKind.growth_trace].owner is ModuleName.field
    assert ownership[ObjectKind.coarse_cover].owner is ModuleName.field
    assert ownership[ObjectKind.gravity_snapshot].owner is ModuleName.field
    assert ownership[ObjectKind.admission_record].owner is ModuleName.admission
    assert ownership[ObjectKind.recall_digest].owner is ModuleName.recall

    assert ownership[ObjectKind.query_probe].durable is False
    assert ownership[ObjectKind.dream_shard].durable is True
    assert ownership[ObjectKind.interpretation_record].durable is True
    assert ownership[ObjectKind.revision_thread].durable is True
    assert ownership[ObjectKind.usage_state_transition].durable is True
    assert ownership[ObjectKind.ledger_event].durable is True
    assert ownership[ObjectKind.admission_record].durable is True
    assert ownership[ObjectKind.admission_record].externally_visible is False
    assert ownership[ObjectKind.gravity_snapshot].externally_visible is False
    assert ownership[ObjectKind.coverage_kernel].externally_visible is False


def test_invariant_ids_are_complete_unique_and_layered() -> None:
    invariants = {item.identifier: item for item in INVARIANTS}
    assert list(invariants) == [f"I-V2-{index:03d}" for index in range(1, 11)]
    assert invariants["I-V2-001"].enforcement_layer is ModuleName.evidence
    assert invariants["I-V2-002"].enforcement_layer is ModuleName.cortex
    assert invariants["I-V2-003"].enforcement_layer is ModuleName.geometry
    assert invariants["I-V2-004"].enforcement_layer is ModuleName.geometry
    assert invariants["I-V2-005"].enforcement_layer is ModuleName.field
    assert invariants["I-V2-006"].enforcement_layer is ModuleName.cortex
    assert invariants["I-V2-007"].enforcement_layer is ModuleName.geometry
    assert invariants["I-V2-008"].enforcement_layer is ModuleName.validation
    assert invariants["I-V2-009"].enforcement_layer is ModuleName.adapters
    assert invariants["I-V2-010"].enforcement_layer is ModuleName.protocol
    da1 = {item.identifier: item for item in DA1_ADMISSION_INVARIANTS}
    assert list(da1) == ["I-V2-DA1-001", "I-V2-DA1-002", "I-V2-DA1-003"]
    assert all(item.enforcement_layer is ModuleName.admission for item in da1.values())
    de1 = {item.identifier: item for item in DE1_MEMORY_SUBSTRATE_INVARIANTS}
    assert list(de1) == [f"I-V2-{index:03d}" for index in range(19, 26)]
    assert all(item.enforcement_layer is ModuleName.evidence for item in de1.values())


def test_v2_object_kinds_do_not_reintroduce_legacy_tree_or_anchor_terms() -> None:
    forbidden = {"parent", "children", "folder", "anchor", "semantic_search"}
    values = {item.value for item in ObjectKind}
    assert not (values & forbidden)
