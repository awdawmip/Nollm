"""Auditable GRF stitching proposal and record objects."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .bridge_kernel import BridgeKernel
from .fixed_point import Q16_ONE

WITNESS_TYPES = frozenset(
    {
        "manual_bridge",
        "source_backed_ref",
        "reuse_observed",
        "coverage_resonance",
        "boundary_overlap",
        "co_activation",
        "lexical_hint",
        "llm_semantic_suggestion",
    }
)
STRONG_WITNESSES = frozenset({"manual_bridge", "source_backed_ref", "reuse_observed"})
MEDIUM_WITNESSES = frozenset({"coverage_resonance", "boundary_overlap", "co_activation"})
WEAK_WITNESSES = frozenset({"lexical_hint", "llm_semantic_suggestion"})
PROPOSAL_STATES = frozenset({"proposed", "accepted", "rejected", "expired"})
ACCEPTED_BY = frozenset({"human", "host_rule", "validation_fixture", "llm_assisted_review"})
ACCEPT_THRESHOLD_Q16 = (Q16_ONE * 3) // 4
LOW_RESIDUAL_Q16 = Q16_ONE // 16


@dataclass(frozen=True, order=True)
class StitchTransform:
    type: str
    values: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.type == "translation":
            if len(self.values) != 2:
                raise ValueError("translation requires dq, dr")
        elif self.type == "eisenstein_similarity":
            if len(self.values) != 4:
                raise ValueError("eisenstein_similarity requires a, b, tq, tr")
        elif self.type == "fixed_point_similarity":
            if len(self.values) != 6:
                raise ValueError("fixed_point_similarity requires four matrix and two translation Q16 values")
        else:
            raise ValueError("unknown transform type")
        if any(type(value) is not int for value in self.values):
            raise TypeError("transform values must be integers")

    @staticmethod
    def translation(dq: int, dr: int) -> "StitchTransform":
        return StitchTransform("translation", (dq, dr))

    @staticmethod
    def eisenstein_similarity(a: int, b: int, tq: int, tr: int) -> "StitchTransform":
        return StitchTransform("eisenstein_similarity", (a, b, tq, tr))

    @staticmethod
    def fixed_point_similarity(matrix_q16: tuple[int, int, int, int], translation_q16: tuple[int, int]) -> "StitchTransform":
        if len(matrix_q16) != 4 or len(translation_q16) != 2:
            raise ValueError("fixed_point_similarity requires 4 matrix and 2 translation values")
        return StitchTransform("fixed_point_similarity", (*matrix_q16, *translation_q16))

    def to_mapping(self) -> dict[str, object]:
        if self.type == "translation":
            return {"type": self.type, "dq": self.values[0], "dr": self.values[1]}
        if self.type == "eisenstein_similarity":
            return {"type": self.type, "a": self.values[0], "b": self.values[1], "tq": self.values[2], "tr": self.values[3]}
        return {"type": self.type, "matrix_q16": self.values[:4], "translation_q16": self.values[4:]}


@dataclass(frozen=True, order=True)
class StitchWitness:
    type: str
    strength_q16: int
    refs: tuple[str, ...]
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.type not in WITNESS_TYPES:
            raise ValueError("unknown witness type")
        if type(self.strength_q16) is not int or self.strength_q16 < 0 or self.strength_q16 > Q16_ONE:
            raise ValueError("strength_q16 must be in Q16 range")
        if not self.refs or any(not isinstance(ref, str) or ref == "" for ref in self.refs):
            raise ValueError("witness refs must be non-empty text")
        if not isinstance(self.metadata, tuple) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in self.metadata):
            raise TypeError("metadata must be stable text pairs")

    def to_mapping(self) -> dict[str, object]:
        return {
            "type": self.type,
            "strength_q16": self.strength_q16,
            "refs": tuple(sorted(self.refs)),
            "metadata": tuple(sorted(self.metadata)),
        }


@dataclass(frozen=True)
class StitchProposal:
    proposal_id: str
    from_patch: str
    to_patch: str
    candidate_transform: StitchTransform
    witnesses: tuple[StitchWitness, ...]
    confidence_q16: int
    state: str
    expires_at: str | None = None

    def __post_init__(self) -> None:
        for label, value in (("proposal_id", self.proposal_id), ("from_patch", self.from_patch), ("to_patch", self.to_patch)):
            if not isinstance(value, str) or value == "":
                raise ValueError(f"{label} must be non-empty text")
        if self.from_patch == self.to_patch:
            raise ValueError("proposal patches must be distinct")
        if not isinstance(self.candidate_transform, StitchTransform):
            raise TypeError("candidate_transform must be StitchTransform")
        if not self.witnesses:
            raise ValueError("witnesses cannot be empty")
        if type(self.confidence_q16) is not int or self.confidence_q16 < 0 or self.confidence_q16 > Q16_ONE:
            raise ValueError("confidence_q16 must be in Q16 range")
        if self.state not in PROPOSAL_STATES:
            raise ValueError("unknown proposal state")
        if self.state == "accepted" and not can_accept(self):
            raise ValueError("proposal lacks acceptance support")

    def accept(self, residual_q16: int) -> "StitchProposal":
        if can_accept(self, residual_q16):
            return replace(self, state="accepted")
        return replace(self, state="rejected")

    def reject(self) -> "StitchProposal":
        return replace(self, state="rejected")

    def to_mapping(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "from_patch": self.from_patch,
            "to_patch": self.to_patch,
            "candidate_transform": self.candidate_transform.to_mapping(),
            "witnesses": tuple(witness.to_mapping() for witness in sorted(self.witnesses, key=lambda item: item.to_mapping()["type"])),
            "confidence_q16": self.confidence_q16,
            "state": self.state,
            "expires_at": self.expires_at,
            "not_fact_merge": True,
            "not_source_mutation": True,
        }


@dataclass(frozen=True)
class StitchRecord:
    stitch_id: str
    proposal_id: str
    accepted_by: str
    accepted_at: str
    from_patch: str
    to_patch: str
    transform: StitchTransform
    residual_q16: int
    bridge_kernel: BridgeKernel
    evidence_refs: tuple[str, ...]
    reversible: bool = True

    def __post_init__(self) -> None:
        for label, value in (("stitch_id", self.stitch_id), ("proposal_id", self.proposal_id), ("accepted_at", self.accepted_at)):
            if not isinstance(value, str) or value == "":
                raise ValueError(f"{label} must be non-empty text")
        if self.accepted_by not in ACCEPTED_BY:
            raise ValueError("unknown accepted_by")
        if type(self.residual_q16) is not int or self.residual_q16 < 0 or self.residual_q16 > Q16_ONE:
            raise ValueError("residual_q16 must be in Q16 range")
        if not isinstance(self.transform, StitchTransform):
            raise TypeError("transform must be StitchTransform")
        if not isinstance(self.bridge_kernel, BridgeKernel):
            raise TypeError("bridge_kernel must be BridgeKernel")
        if self.bridge_kernel.from_patch != self.from_patch or self.bridge_kernel.to_patch != self.to_patch:
            raise ValueError("bridge kernel patch endpoints must match stitch record")
        if not self.evidence_refs or any(not isinstance(ref, str) or ref == "" for ref in self.evidence_refs):
            raise ValueError("evidence_refs must be non-empty text")
        if type(self.reversible) is not bool:
            raise TypeError("reversible must be bool")

    @classmethod
    def from_accepted_proposal(
        cls,
        stitch_id: str,
        proposal: StitchProposal,
        accepted_by: str,
        accepted_at: str,
        residual_q16: int,
        bridge_kernel: BridgeKernel,
    ) -> "StitchRecord":
        if proposal.state != "accepted":
            raise ValueError("cannot create stitch record from non-accepted proposal")
        if bridge_kernel.from_patch != proposal.from_patch or bridge_kernel.to_patch != proposal.to_patch:
            raise ValueError("bridge kernel patch endpoints must match proposal")
        evidence_refs = tuple(sorted({ref for witness in proposal.witnesses for ref in witness.refs}))
        return cls(
            stitch_id,
            proposal.proposal_id,
            accepted_by,
            accepted_at,
            proposal.from_patch,
            proposal.to_patch,
            proposal.candidate_transform,
            residual_q16,
            bridge_kernel,
            evidence_refs,
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "stitch_id": self.stitch_id,
            "proposal_id": self.proposal_id,
            "accepted_by": self.accepted_by,
            "accepted_at": self.accepted_at,
            "from_patch": self.from_patch,
            "to_patch": self.to_patch,
            "transform": self.transform.to_mapping(),
            "residual_q16": self.residual_q16,
            "bridge_kernel": self.bridge_kernel.to_mapping(),
            "evidence_refs": tuple(sorted(self.evidence_refs)),
            "reversible": self.reversible,
            "not_fact_merge": True,
            "not_parent_child": True,
        }


def can_accept(proposal: StitchProposal, residual_q16: int = 0) -> bool:
    types = {witness.type for witness in proposal.witnesses}
    if types <= WEAK_WITNESSES:
        return False
    if types & STRONG_WITNESSES:
        return True
    if (types & MEDIUM_WITNESSES) and len(types & MEDIUM_WITNESSES) >= 2:
        return proposal.confidence_q16 >= ACCEPT_THRESHOLD_Q16 and residual_q16 <= LOW_RESIDUAL_Q16
    return False
