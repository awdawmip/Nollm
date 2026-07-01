from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any

from nollm.dream_geometry.admission import (
    AdmissionPlacementPlan,
    AdmissionRequest,
    AxisPlacement,
    MemoryAdmissionOrchestrator,
    open_store as open_admission_store,
)
from nollm.dream_geometry.cortex import open_store as open_cortex_store
from nollm.dream_geometry.evidence import DreamShard, OriginDescriptor, TemporalContext, open_store as open_evidence_store
from nollm.dream_geometry.geometry import AxialCoord, LocalChart, Vec2, make_hex_cell
from nollm.dream_geometry.protocol.contracts import GrowthBasis, OriginKind, UsageState


RECORDED_AT = "2026-07-01T00:00:00+00:00"
SHARD_ID = "shard:da1:synthetic-weather"
PROPOSAL_ID = "gp_da1_synthetic_weather"
ADMISSION_ID = "adm_da1_synthetic_weather"


def build_environment(root: Path):
    evidence = open_evidence_store(root / "evidence")
    cortex = open_cortex_store(root / "cortex", evidence)
    admission = open_admission_store(root / "admission", evidence, cortex)
    return evidence, cortex, admission, MemoryAdmissionOrchestrator(evidence, cortex, admission)


def build_request(
    *,
    admission_id: str = ADMISSION_ID,
    proposal_id: str = PROPOSAL_ID,
    axes: tuple[tuple[str, str], ...] = (("location", "Kunming"), ("phenomenon", "rain")),
    plan_order: str = "normal",
) -> AdmissionRequest:
    content = "Kunming rain synthetic shard."
    shard = DreamShard(
        SHARD_ID,
        content,
        OriginDescriptor(OriginKind.system_seed, "synthetic:da1", None, None),
        TemporalContext(RECORDED_AT, None, RECORDED_AT, "en-US"),
        (),
        UsageState.active,
    )
    growth_axes = []
    placements = []
    chart = LocalChart("da1:chart", 0, 1.0, 0.0, Vec2(0.0, 0.0))
    source = make_hex_cell(chart, AxialCoord(0, 0))
    target = make_hex_cell(chart, AxialCoord(0, 0))
    for axis_id, expression in axes:
        start = content.index(expression)
        step_id = f"step_da1_{axis_id}"
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
                                "record_id": SHARD_ID,
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
        placements.append(AxisPlacement(axis_id, step_id, source, (target,), None))
    if plan_order == "reverse":
        placements = list(reversed(placements))
    request = AdmissionRequest(
        admission_id,
        shard,
        {
            "contract_version": "dc1.v1",
            "proposal_id": proposal_id,
            "subject_shard_id": SHARD_ID,
            "submitted_at": RECORDED_AT,
            "budget": {"max_axes": 4, "max_total_steps": 8, "max_ray_steps": 4},
            "do_not_infer": ["synthetic DA1 fixture only"],
            "forbidden_inferences": ["no semantic fallback"],
            "possible_conflict_refs": [],
            "axes": growth_axes,
        },
        AdmissionPlacementPlan("apl_da1_synthetic_weather", tuple(placements)),
        RECORDED_AT,
    )
    return request


def tree_manifest(root: Path) -> tuple[tuple[str, str], ...]:
    root = Path(root)
    if not root.exists():
        return ()
    return tuple(
        sorted(
            (path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest())
            for path in root.rglob("*")
            if path.is_file()
        )
    )


def mutate_request(request: AdmissionRequest, **updates: Any) -> AdmissionRequest:
    return replace(request, **updates)
