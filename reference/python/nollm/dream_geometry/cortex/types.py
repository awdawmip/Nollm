"""Immutable DC1 Cortex Compiler value objects and canonical payloads."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from nollm.dream_geometry.protocol.contracts import GrowthBasis

CONTRACT_VERSION = "dc1.v1"


class CompilationDecision(Enum):
    accepted = "accepted"
    rejected = "rejected"


@dataclass(frozen=True)
class TextSpanRef:
    record_id: str
    start_char: int
    end_char: int
    quoted_text: str


@dataclass(frozen=True)
class RuleReference:
    rule_id: str
    rule_version: str
    rule_label: str
    source_ref: str | None


@dataclass(frozen=True)
class StepReference:
    input_step_id: str


@dataclass(frozen=True)
class GrowthStep:
    step_id: str
    expression: str
    basis: GrowthBasis | str
    basis_refs: tuple[TextSpanRef | RuleReference | StepReference, ...]
    rationale: str | None
    provisional_only: bool


@dataclass(frozen=True)
class AxisRay:
    axis_id: str
    ray: tuple[GrowthStep, ...]


@dataclass(frozen=True)
class CompilationBudget:
    max_axes: int
    max_total_steps: int
    max_ray_steps: int


@dataclass(frozen=True)
class QueryBudget:
    max_axes: int
    max_charts: int
    max_layers: int
    max_cells_per_layer: int


@dataclass(frozen=True)
class CompiledGrowthProposal:
    proposal_id: str
    subject_shard_id: str
    axes: tuple[AxisRay, ...]
    budget: CompilationBudget
    do_not_infer: tuple[str, ...]
    forbidden_inferences: tuple[str, ...]
    possible_conflict_refs: tuple[str, ...]
    submitted_at: str | None
    contract_version: str = CONTRACT_VERSION


@dataclass(frozen=True)
class CompiledQueryProbe:
    probe_id: str
    query_text: str
    axes: tuple[AxisRay, ...]
    budget: QueryBudget
    do_not_infer: tuple[str, ...]
    forbidden_inferences: tuple[str, ...]
    reference_instant: str | None
    requires_runtime_resolution: bool
    ephemeral: bool = True
    contract_version: str = CONTRACT_VERSION


@dataclass(frozen=True)
class CompilationReceipt:
    receipt_id: str
    kind: str
    proposal_id: str
    decision: CompilationDecision
    reason_codes: tuple[str, ...]
    submitted_payload_fingerprint: str
    normalized_payload_fingerprint: str | None
    submitted_at: str | None
    input_snapshot: dict[str, Any]
    contract_version: str = CONTRACT_VERSION


def canonical_payload(value: object) -> dict[str, Any]:
    if isinstance(value, TextSpanRef):
        return {
            "ref_type": "text_span",
            "record_id": value.record_id,
            "start_char": value.start_char,
            "end_char": value.end_char,
            "quoted_text": value.quoted_text,
        }
    if isinstance(value, RuleReference):
        return {
            "ref_type": "rule",
            "rule_id": value.rule_id,
            "rule_version": value.rule_version,
            "rule_label": value.rule_label,
            "source_ref": value.source_ref,
        }
    if isinstance(value, StepReference):
        return {"ref_type": "step", "input_step_id": value.input_step_id}
    if isinstance(value, GrowthStep):
        return {
            "step_id": value.step_id,
            "expression": value.expression,
            "basis": value.basis.value if isinstance(value.basis, GrowthBasis) else value.basis,
            "basis_refs": tuple(canonical_payload(ref) for ref in value.basis_refs),
            "rationale": value.rationale,
            "provisional_only": value.provisional_only,
        }
    if isinstance(value, AxisRay):
        return {"axis_id": value.axis_id, "ray": tuple(canonical_payload(step) for step in value.ray)}
    if isinstance(value, CompilationBudget):
        return {
            "max_axes": value.max_axes,
            "max_total_steps": value.max_total_steps,
            "max_ray_steps": value.max_ray_steps,
        }
    if isinstance(value, QueryBudget):
        return {
            "max_axes": value.max_axes,
            "max_charts": value.max_charts,
            "max_layers": value.max_layers,
            "max_cells_per_layer": value.max_cells_per_layer,
        }
    if isinstance(value, CompiledGrowthProposal):
        return {
            "record_type": "compiled_growth_proposal",
            "contract_version": value.contract_version,
            "proposal_id": value.proposal_id,
            "subject_shard_id": value.subject_shard_id,
            "axes": tuple(canonical_payload(axis) for axis in value.axes),
            "budget": canonical_payload(value.budget),
            "do_not_infer": value.do_not_infer,
            "forbidden_inferences": value.forbidden_inferences,
            "possible_conflict_refs": value.possible_conflict_refs,
            "submitted_at": value.submitted_at,
            "provisional_only_present": any(step.provisional_only for axis in value.axes for step in axis.ray),
        }
    if isinstance(value, CompiledQueryProbe):
        return {
            "record_type": "compiled_query_probe",
            "contract_version": value.contract_version,
            "probe_id": value.probe_id,
            "query_text": value.query_text,
            "axes": tuple(canonical_payload(axis) for axis in value.axes),
            "budget": canonical_payload(value.budget),
            "do_not_infer": value.do_not_infer,
            "forbidden_inferences": value.forbidden_inferences,
            "reference_instant": value.reference_instant,
            "requires_runtime_resolution": value.requires_runtime_resolution,
            "ephemeral": value.ephemeral,
        }
    if isinstance(value, CompilationReceipt):
        return {
            "record_type": "compilation_receipt",
            "contract_version": value.contract_version,
            "receipt_id": value.receipt_id,
            "kind": value.kind,
            "proposal_id": value.proposal_id,
            "decision": value.decision.value,
            "reason_codes": value.reason_codes,
            "submitted_payload_fingerprint": value.submitted_payload_fingerprint,
            "normalized_payload_fingerprint": value.normalized_payload_fingerprint,
            "submitted_at": value.submitted_at,
            "input_snapshot": value.input_snapshot,
        }
    raise TypeError(f"unsupported canonical payload type: {type(value).__name__}")


def canonical_json(value: object) -> str:
    return json.dumps(canonical_payload(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_mapping_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def payload_fingerprint(value: object | dict[str, Any]) -> str:
    rendered = canonical_mapping_json(value) if isinstance(value, dict) else canonical_json(value)
    return "sha256:" + sha256(rendered.encode("utf-8")).hexdigest()


__all__ = [
    "CONTRACT_VERSION",
    "AxisRay",
    "CompilationBudget",
    "CompilationDecision",
    "CompilationReceipt",
    "CompiledGrowthProposal",
    "CompiledQueryProbe",
    "GrowthStep",
    "QueryBudget",
    "RuleReference",
    "StepReference",
    "TextSpanRef",
    "canonical_json",
    "canonical_mapping_json",
    "canonical_payload",
    "payload_fingerprint",
]
