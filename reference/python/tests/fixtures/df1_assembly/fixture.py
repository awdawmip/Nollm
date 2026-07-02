from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from nollm.dream_geometry.admission import AdmissionPlacementPlan, AdmissionRequest, AxisPlacement, MemoryAdmissionOrchestrator, open_store as open_admission_store
from nollm.dream_geometry.assembly import AdmissionReplaySource, FiniteAdmissionSet
from nollm.dream_geometry.cortex import open_store as open_cortex_store
from nollm.dream_geometry.evidence import DreamShard, OriginDescriptor, TemporalContext, open_store as open_evidence_store
from nollm.dream_geometry.field import VerifiedChartLink
from nollm.dream_geometry.geometry import AxialCoord, LocalChart, Vec2, make_hex_cell
from nollm.dream_geometry.geometry.transform import SimilarityTransform, TransformWitness, validate_transform
from nollm.dream_geometry.protocol.contracts import GrowthBasis, OriginKind, UsageState


RECORDED_AT = "2026-07-02T00:00:00+08:00"


def build_df1_environment(root: Path, specs=(("adm_df1_alpha", "shard:df1:alpha", "gp_df1_alpha", "Kunming rain alpha."),)):
    evidence = open_evidence_store(root / "evidence")
    cortex = open_cortex_store(root / "cortex", evidence)
    admission = open_admission_store(root / "admission", evidence, cortex)
    orchestrator = MemoryAdmissionOrchestrator(evidence, cortex, admission)
    for admission_id, shard_id, proposal_id, content in specs:
        orchestrator.admit(build_request(admission_id, shard_id, proposal_id, content))
    reopened = open_admission_store(root / "admission", evidence, cortex, orchestrator.validate_replay_record)
    return evidence, cortex, reopened, MemoryAdmissionOrchestrator(evidence, cortex, reopened)


def admission_sources(evidence, cortex, admission, orchestrator, admission_ids: tuple[str, ...], *, include_projection: bool = False) -> tuple[AdmissionReplaySource, ...]:
    receipts = {receipt.receipt_id: receipt for receipt in cortex.receipts()}
    sources = []
    for admission_id in admission_ids:
        record = admission.get_admission_record(admission_id)
        sources.append(
            AdmissionReplaySource(
                record,
                evidence,
                cortex,
                orchestrator.replay_record,
                receipts[record.compilation_receipt_id],
                orchestrator.replay_record(record) if include_projection else None,
            )
        )
    return tuple(sources)


def finite_set(evidence, cortex, admission, orchestrator, admission_ids: tuple[str, ...], assembly_id: str = "df1_fixture") -> FiniteAdmissionSet:
    return FiniteAdmissionSet(assembly_id, admission_sources(evidence, cortex, admission, orchestrator, admission_ids))


def finite_projected_set(evidence, cortex, admission, orchestrator, admission_ids: tuple[str, ...], assembly_id: str = "df1_projected_fixture") -> FiniteAdmissionSet:
    return FiniteAdmissionSet(assembly_id, admission_sources(evidence, cortex, admission, orchestrator, admission_ids, include_projection=True))


def build_request(admission_id: str, shard_id: str, proposal_id: str, content: str, *, cross_chart: bool = False) -> AdmissionRequest:
    shard = DreamShard(
        shard_id,
        content,
        OriginDescriptor(OriginKind.system_seed, "synthetic:df1", None, None),
        TemporalContext(RECORDED_AT, None, RECORDED_AT, "en-US"),
        (),
        UsageState.active,
    )
    axes = (("location", "Kunming"), ("phenomenon", "rain"))
    growth_axes = []
    placements = []
    source_chart = LocalChart("df1:fine", 0, 1.0, 0.0, Vec2(0.0, 0.0))
    target_chart = LocalChart("df1:coarse", 0, 1.0, 0.0, Vec2(0.0, 0.0)) if cross_chart else source_chart
    source = make_hex_cell(source_chart, AxialCoord(0, 0))
    target = make_hex_cell(target_chart, AxialCoord(0, 0))
    link = VerifiedChartLink(source.chart_fingerprint, target.chart_fingerprint, verified_transform()) if cross_chart else None
    for axis_id, expression in axes:
        start = content.index(expression)
        step_id = f"step_{proposal_id}_{axis_id}"
        growth_axes.append(
            {
                "axis_id": axis_id,
                "ray": [
                    {
                        "step_id": step_id,
                        "expression": expression,
                        "basis": GrowthBasis.explicit_in_shard.value,
                        "basis_refs": [
                            {
                                "ref_type": "text_span",
                                "record_id": shard_id,
                                "start_char": start,
                                "end_char": start + len(expression),
                                "quoted_text": expression,
                            }
                        ],
                        "rationale": None,
                    }
                ],
            }
        )
        placements.append(AxisPlacement(axis_id, step_id, source, (target,), link))
    return AdmissionRequest(
        admission_id,
        shard,
        {
            "contract_version": "dc1.v1",
            "proposal_id": proposal_id,
            "subject_shard_id": shard_id,
            "submitted_at": RECORDED_AT,
            "budget": {"max_axes": 4, "max_total_steps": 8, "max_ray_steps": 4},
            "do_not_infer": ["synthetic DF1 fixture only"],
            "forbidden_inferences": ["no semantic fallback"],
            "possible_conflict_refs": [],
            "axes": growth_axes,
        },
        AdmissionPlacementPlan("apl_" + admission_id.removeprefix("adm_"), tuple(placements)),
        RECORDED_AT,
    )


def verified_transform():
    return validate_transform(
        SimilarityTransform(1.0, 0.0, Vec2(0.0, 0.0)),
        (
            TransformWitness(Vec2(0.0, 0.0), Vec2(0.0, 0.0)),
            TransformWitness(Vec2(1.0, 0.0), Vec2(1.0, 0.0)),
            TransformWitness(Vec2(0.0, 1.0), Vec2(0.0, 1.0)),
        ),
        1.0,
    )


def tree_manifest(root: Path) -> tuple[tuple[str, str], ...]:
    root = Path(root)
    if not root.exists():
        return ()
    return tuple(sorted((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest()) for path in root.rglob("*") if path.is_file()))


def replace_record(record, **updates):
    return replace(record, **updates)
