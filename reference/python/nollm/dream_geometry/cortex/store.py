"""DC1 file-first Cortex store for compiled Growth Proposals."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from nollm.dream_geometry.evidence import MemorySubstrateStore

from .compiler import compile_growth
from .errors import (
    DC1_CORTEX_ROOT_EQUALS_EVIDENCE_ROOT,
    DC1_ON_DISK_CONTRACT_VIOLATION,
    DC1_PROPOSAL_ID_PAYLOAD_CONFLICT,
    DC1_RECEIPT_PROPOSAL_MISMATCH,
    DC1Rejection,
    reject,
)
from .types import (
    CONTRACT_VERSION,
    AxisRay,
    CompilationBudget,
    CompilationDecision,
    CompilationReceipt,
    CompiledGrowthProposal,
    GrowthStep,
    RuleReference,
    StepReference,
    TextSpanRef,
    canonical_json,
    canonical_mapping_json,
    payload_fingerprint,
)


@dataclass(frozen=True)
class CompileGrowthResult:
    proposal: CompiledGrowthProposal
    receipt: CompilationReceipt
    created: bool
    idempotent: bool


class CortexStore:
    """Single-process DC1 store, separate from the DE1 evidence root."""

    def __init__(self, cortex_root: Path, evidence_store: MemorySubstrateStore):
        self.root = Path(cortex_root).resolve()
        self.evidence_store = evidence_store
        evidence_root = Path(evidence_store.root).resolve()
        if self.root == evidence_root:
            reject(DC1_CORTEX_ROOT_EQUALS_EVIDENCE_ROOT, "cortex_root must differ from evidence_root")
        self.proposals_dir = self.root / "compiled_growth_proposals"
        self.receipts_dir = self.root / "compilation_receipts"
        self.root.mkdir(parents=True, exist_ok=True)
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        self.receipts_dir.mkdir(parents=True, exist_ok=True)
        self._format_path = self.root / "format.json"
        self._ensure_format()
        self._validate_store()

    def compile_growth(self, submission: dict[str, Any]) -> CompileGrowthResult:
        submitted_key = payload_fingerprint(submission)
        proposal = compile_growth(submission, self.evidence_store)
        normalized_key = payload_fingerprint(proposal)
        proposal_path = self._proposal_path(proposal.proposal_id)
        receipt = _accepted_receipt(proposal, submission, submitted_key, normalized_key)
        receipt_path = self._receipt_path(receipt.receipt_id)
        if proposal_path.exists():
            existing_text = proposal_path.read_text(encoding="utf-8")
            if existing_text != canonical_json(proposal):
                reject(DC1_PROPOSAL_ID_PAYLOAD_CONFLICT, "same proposal_id has different normalized payload")
            if not receipt_path.exists() or receipt_path.read_text(encoding="utf-8") != canonical_json(receipt):
                reject(DC1_RECEIPT_PROPOSAL_MISMATCH, "idempotent proposal receipt mismatch")
            return CompileGrowthResult(proposal, receipt, False, True)
        if any(_receipt_from_payload(_read_json(path)).proposal_id == proposal.proposal_id for path in self.receipts_dir.glob("*.json")):
            reject(DC1_PROPOSAL_ID_PAYLOAD_CONFLICT, "same proposal_id already has receipt")
        _atomic_write_text(proposal_path, canonical_json(proposal))
        _atomic_write_text(receipt_path, canonical_json(receipt))
        return CompileGrowthResult(proposal, receipt, True, False)

    def get_growth_proposal(self, proposal_id: str) -> CompiledGrowthProposal:
        return _proposal_from_payload(_read_json(self._proposal_path(proposal_id)))

    def receipts(self) -> tuple[CompilationReceipt, ...]:
        return tuple(_receipt_from_payload(_read_json(path)) for path in sorted(self.receipts_dir.glob("*.json")))

    def _proposal_path(self, proposal_id: str) -> Path:
        return self.proposals_dir / f"{_name_key(proposal_id)}.json"

    def _receipt_path(self, receipt_id: str) -> Path:
        return self.receipts_dir / f"{_name_key(receipt_id)}.json"

    def _ensure_format(self) -> None:
        payload = {"format_version": CONTRACT_VERSION, "store_kind": "cortex_compiler"}
        rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if self._format_path.exists():
            if self._format_path.read_text(encoding="utf-8") != rendered:
                reject(DC1_ON_DISK_CONTRACT_VIOLATION, "unsupported cortex store format")
            return
        _atomic_write_text(self._format_path, rendered)

    def _validate_store(self) -> None:
        proposals: dict[str, CompiledGrowthProposal] = {}
        for path in sorted(self.proposals_dir.glob("*.json")):
            try:
                proposal = _proposal_from_payload(_read_json(path))
                if path != self._proposal_path(proposal.proposal_id):
                    reject(DC1_ON_DISK_CONTRACT_VIOLATION, "proposal filename mismatch")
                if proposal.proposal_id in proposals:
                    reject(DC1_ON_DISK_CONTRACT_VIOLATION, "duplicate proposal id")
                self.evidence_store.get_dream_shard(proposal.subject_shard_id)
                _validate_proposal_refs(self.evidence_store, proposal)
                proposals[proposal.proposal_id] = proposal
            except DC1Rejection:
                raise
            except Exception as exc:
                raise DC1Rejection((DC1_ON_DISK_CONTRACT_VIOLATION,), "invalid proposal on disk") from exc
        accepted_receipts: dict[str, CompilationReceipt] = {}
        for path in sorted(self.receipts_dir.glob("*.json")):
            try:
                receipt = _receipt_from_payload(_read_json(path))
                if path != self._receipt_path(receipt.receipt_id):
                    reject(DC1_ON_DISK_CONTRACT_VIOLATION, "receipt filename mismatch")
                if receipt.decision is CompilationDecision.accepted:
                    proposal = proposals.get(receipt.proposal_id)
                    if proposal is None:
                        reject(DC1_RECEIPT_PROPOSAL_MISMATCH, "accepted receipt without proposal")
                    if receipt.normalized_payload_fingerprint != payload_fingerprint(proposal):
                        reject(DC1_RECEIPT_PROPOSAL_MISMATCH, "receipt proposal fingerprint mismatch")
                    if receipt.proposal_id in accepted_receipts:
                        reject(DC1_ON_DISK_CONTRACT_VIOLATION, "duplicate accepted receipt")
                    accepted_receipts[receipt.proposal_id] = receipt
            except DC1Rejection:
                raise
            except Exception as exc:
                raise DC1Rejection((DC1_ON_DISK_CONTRACT_VIOLATION,), "invalid receipt on disk") from exc
        missing = set(proposals) - set(accepted_receipts)
        if missing:
            reject(DC1_RECEIPT_PROPOSAL_MISMATCH, "proposal missing accepted receipt")


def open_store(cortex_root: Path, evidence_store: MemorySubstrateStore) -> CortexStore:
    return CortexStore(cortex_root, evidence_store)


def _accepted_receipt(proposal: CompiledGrowthProposal, submission: dict[str, Any], submitted_key: str, normalized_key: str) -> CompilationReceipt:
    receipt_seed = canonical_mapping_json({"proposal_id": proposal.proposal_id, "submitted": submitted_key, "normalized": normalized_key})
    receipt_id = "cr_" + sha256(receipt_seed.encode("utf-8")).hexdigest()[:32]
    return CompilationReceipt(receipt_id, "growth", proposal.proposal_id, CompilationDecision.accepted, (), submitted_key, normalized_key, proposal.submitted_at, submission)


def _validate_proposal_refs(evidence_store: MemorySubstrateStore, proposal: CompiledGrowthProposal) -> None:
    for axis in proposal.axes:
        for step in axis.ray:
            for ref in step.basis_refs:
                if isinstance(ref, TextSpanRef) and ref.record_id != proposal.subject_shard_id:
                    evidence_store.get_dream_shard(ref.record_id)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        reject(DC1_ON_DISK_CONTRACT_VIOLATION, "on-disk JSON must be object")
    return payload


def _proposal_from_payload(payload: dict[str, Any]) -> CompiledGrowthProposal:
    _exact_keys(
        payload,
        {
            "record_type",
            "contract_version",
            "proposal_id",
            "subject_shard_id",
            "axes",
            "budget",
            "do_not_infer",
            "forbidden_inferences",
            "submitted_at",
            "provisional_only_present",
        },
    )
    if payload["record_type"] != "compiled_growth_proposal" or payload["contract_version"] != CONTRACT_VERSION:
        reject(DC1_ON_DISK_CONTRACT_VIOLATION, "invalid proposal record type")
    proposal = CompiledGrowthProposal(
        payload["proposal_id"],
        payload["subject_shard_id"],
        tuple(_axis_from_payload(axis) for axis in payload["axes"]),
        _budget_from_payload(payload["budget"]),
        tuple(payload["do_not_infer"]),
        tuple(payload["forbidden_inferences"]),
        payload["submitted_at"],
    )
    if payload != json.loads(canonical_json(proposal)):
        reject(DC1_ON_DISK_CONTRACT_VIOLATION, "proposal canonical payload mismatch")
    return proposal


def _receipt_from_payload(payload: dict[str, Any]) -> CompilationReceipt:
    _exact_keys(payload, {"record_type", "contract_version", "receipt_id", "kind", "proposal_id", "decision", "reason_codes", "submitted_payload_fingerprint", "normalized_payload_fingerprint", "submitted_at", "input_snapshot"})
    if payload["record_type"] != "compilation_receipt" or payload["contract_version"] != CONTRACT_VERSION:
        reject(DC1_ON_DISK_CONTRACT_VIOLATION, "invalid receipt record type")
    receipt = CompilationReceipt(payload["receipt_id"], payload["kind"], payload["proposal_id"], CompilationDecision(payload["decision"]), tuple(payload["reason_codes"]), payload["submitted_payload_fingerprint"], payload["normalized_payload_fingerprint"], payload["submitted_at"], payload["input_snapshot"])
    if payload != json.loads(canonical_json(receipt)):
        reject(DC1_ON_DISK_CONTRACT_VIOLATION, "receipt canonical payload mismatch")
    return receipt


def _axis_from_payload(payload: dict[str, Any]) -> AxisRay:
    _exact_keys(payload, {"axis_id", "ray"})
    return AxisRay(payload["axis_id"], tuple(_step_from_payload(step) for step in payload["ray"]))


def _step_from_payload(payload: dict[str, Any]) -> GrowthStep:
    _exact_keys(payload, {"step_id", "expression", "basis", "basis_refs", "rationale", "provisional_only"})
    from nollm.dream_geometry.protocol.contracts import GrowthBasis

    basis = payload["basis"] if payload["basis"] == "explicit_in_query" else GrowthBasis(payload["basis"])
    return GrowthStep(payload["step_id"], payload["expression"], basis, tuple(_ref_from_payload(ref) for ref in payload["basis_refs"]), payload["rationale"], payload["provisional_only"])


def _ref_from_payload(payload: dict[str, Any]) -> TextSpanRef | RuleReference | StepReference:
    ref_type = payload.get("ref_type")
    if ref_type == "text_span":
        _exact_keys(payload, {"ref_type", "record_id", "start_char", "end_char", "quoted_text"})
        return TextSpanRef(payload["record_id"], payload["start_char"], payload["end_char"], payload["quoted_text"])
    if ref_type == "rule":
        _exact_keys(payload, {"ref_type", "rule_id", "rule_version", "rule_label", "source_ref"})
        return RuleReference(payload["rule_id"], payload["rule_version"], payload["rule_label"], payload["source_ref"])
    if ref_type == "step":
        _exact_keys(payload, {"ref_type", "input_step_id"})
        return StepReference(payload["input_step_id"])
    reject(DC1_ON_DISK_CONTRACT_VIOLATION, "invalid ref type")


def _budget_from_payload(payload: dict[str, Any]) -> CompilationBudget:
    _exact_keys(payload, {"max_axes", "max_total_steps", "max_ray_steps"})
    return CompilationBudget(payload["max_axes"], payload["max_total_steps"], payload["max_ray_steps"])


def _exact_keys(payload: dict[str, Any], keys: set[str]) -> None:
    if set(payload) != keys:
        reject(DC1_ON_DISK_CONTRACT_VIOLATION, "on-disk contract field mismatch")


def _name_key(record_id: str) -> str:
    return sha256(record_id.encode("utf-8")).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


__all__ = ["CompileGrowthResult", "CortexStore", "open_store"]
