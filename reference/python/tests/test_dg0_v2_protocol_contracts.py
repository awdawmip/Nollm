import dataclasses
import inspect

from nollm.dream_geometry.protocol import contracts
from nollm.dream_geometry.protocol.contracts import (
    ChartTransformState,
    CoverState,
    GrowthBasis,
    INVARIANTS,
    KernelDirection,
    ModuleName,
    OBJECT_OWNERSHIP,
    ObjectKind,
    TraceState,
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
    assert enum_values(ModuleName) == ["protocol", "evidence", "geometry", "field", "cortex", "recall", "adapters", "validation"]
    assert enum_values(ObjectKind) == [
        "dream_shard",
        "growth_proposal",
        "query_probe",
        "local_chart",
        "chart_transform",
        "coverage_kernel",
        "growth_trace",
        "coarse_cover",
        "gravity_snapshot",
        "recall_digest",
        "ledger_event",
    ]


def test_contract_dataclasses_are_frozen_and_do_not_use_any() -> None:
    for name in ["ObjectOwnership", "DependencyRule", "Invariant"]:
        cls = getattr(contracts, name)
        assert dataclasses.is_dataclass(cls)
        assert cls.__dataclass_params__.frozen
        assert "Any" not in inspect.getsource(cls)


def test_object_ownership_mapping_is_complete() -> None:
    ownership = {item.object_kind: item for item in OBJECT_OWNERSHIP}
    assert ownership[ObjectKind.dream_shard].owner is ModuleName.evidence
    assert ownership[ObjectKind.ledger_event].owner is ModuleName.evidence
    assert ownership[ObjectKind.growth_proposal].owner is ModuleName.cortex
    assert ownership[ObjectKind.query_probe].owner is ModuleName.cortex
    assert ownership[ObjectKind.local_chart].owner is ModuleName.geometry
    assert ownership[ObjectKind.chart_transform].owner is ModuleName.geometry
    assert ownership[ObjectKind.coverage_kernel].owner is ModuleName.geometry
    assert ownership[ObjectKind.growth_trace].owner is ModuleName.field
    assert ownership[ObjectKind.coarse_cover].owner is ModuleName.field
    assert ownership[ObjectKind.gravity_snapshot].owner is ModuleName.field
    assert ownership[ObjectKind.recall_digest].owner is ModuleName.recall

    assert ownership[ObjectKind.query_probe].durable is False
    assert ownership[ObjectKind.dream_shard].durable is True
    assert ownership[ObjectKind.ledger_event].durable is True
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


def test_v2_object_kinds_do_not_reintroduce_legacy_tree_or_anchor_terms() -> None:
    forbidden = {"parent", "children", "folder", "anchor", "semantic_search"}
    values = {item.value for item in ObjectKind}
    assert not (values & forbidden)
