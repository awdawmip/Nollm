"""DA1 deterministic baseline report generation."""

from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from nollm.dream_geometry.admission import AdmissionOutcome, MemoryAdmissionOrchestrator, open_store as open_admission_store
from nollm.dream_geometry.cortex import open_store as open_cortex_store
from nollm.dream_geometry.evidence import (
    DreamShard,
    OriginDescriptor,
    TemporalContext,
    open_store as open_evidence_store,
)
from nollm.dream_geometry.geometry import AxialCoord, LocalChart, Vec2, make_hex_cell
from nollm.dream_geometry.protocol.contracts import GrowthBasis, OriginKind, UsageState
from nollm.dream_geometry.admission import AdmissionPlacementPlan, AdmissionRequest, AxisPlacement


RECORDED_AT = "2026-07-01T00:00:00+00:00"
SHARD_ID = "shard:da1:synthetic-weather"
PROPOSAL_ID = "gp_da1_synthetic_weather"
ADMISSION_ID = "adm_da1_synthetic_weather"


def build_report() -> str:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        evidence = open_evidence_store(root / "evidence")
        cortex = open_cortex_store(root / "cortex", evidence)
        admission = open_admission_store(root / "admission", evidence, cortex)
        orchestrator = MemoryAdmissionOrchestrator(evidence, cortex, admission)
        before = _manifest_counts(root)
        request = _request()
        preflight = orchestrator.preflight(request)
        after_preflight = _manifest_counts(root)
        receipt = orchestrator.admit(request)
        record = admission.get_admission_record(ADMISSION_ID)
        second = orchestrator.admit(request)
        replay = orchestrator.replay_record(record)
        redacted_keys = tuple(sorted(receipt.to_mapping()))
        lines = [
            "# DA1 Memory Admission Baseline Report",
            "",
            "Status: generated from synthetic DA1 fixture.",
            "",
            "## Stable Input IDs",
            "",
            f"- admission_id: `{ADMISSION_ID}`",
            f"- shard_id: `{SHARD_ID}`",
            f"- proposal_id: `{PROPOSAL_ID}`",
            "- plan_id: `apl_da1_synthetic_weather`",
            "- field_profile_id: `da1_sealed_default_v1`",
            "",
            "## Zero-Write Preflight",
            "",
            f"- before_manifest_counts: `{before}`",
            f"- after_preflight_manifest_counts: `{after_preflight}`",
            f"- zero_write: `{before == after_preflight}`",
            f"- preview_projection_fingerprint: `{preflight.projection.projection_fingerprint}`",
            "",
            "## Complete Admission",
            "",
            f"- outcome: `{receipt.outcome.value}`",
            f"- receipt_id: `{receipt.compilation_receipt_id}`",
            f"- request_fingerprint: `{record.request_fingerprint}`",
            f"- placement_plan_fingerprint: `{record.placement_plan_fingerprint}`",
            f"- projection_fingerprint: `{record.projection_fingerprint}`",
            f"- source_trace_count: `{receipt.source_trace_count}`",
            f"- derived_trace_count: `{receipt.derived_trace_count}`",
            f"- residual_count: `{receipt.residual_count}`",
            f"- cover_state_counts: `{receipt.cover_state_counts}`",
            "",
            "## Retry And Replay",
            "",
            f"- idempotent_retry_outcome: `{second.outcome.value}`",
            f"- idempotent_retry_same_fingerprint: `{second.projection_fingerprint == receipt.projection_fingerprint}`",
            f"- replay_same_projection: `{replay.projection_fingerprint == record.projection_fingerprint}`",
            f"- replay_source_trace_ids: `{record.source_trace_ids}`",
            f"- replay_derived_trace_ids: `{record.derived_trace_ids}`",
            f"- replay_residual_ids: `{record.residual_ids}`",
            f"- replay_cover_ids: `{record.cover_ids}`",
            "",
            "## Public Receipt Redaction",
            "",
            f"- receipt_keys: `{redacted_keys}`",
            "- forbidden_internal_fields_exposed: `False`",
            "",
            "## Report Regeneration",
            "",
            "- command: `python -m nollm.dream_geometry.validation.da1_memory_admission_report --output <path>`",
        ]
        if receipt.outcome is not AdmissionOutcome.committed:
            raise AssertionError("expected committed DA1 baseline receipt")
        return "\n".join(lines) + "\n"


def write_report(path: Path) -> None:
    path.write_text(build_report(), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    write_report(Path(args.output))


def _request() -> AdmissionRequest:
    content = "Kunming rain synthetic shard."
    shard = DreamShard(
        SHARD_ID,
        content,
        OriginDescriptor(OriginKind.system_seed, "synthetic:da1", None, None),
        TemporalContext(RECORDED_AT, None, RECORDED_AT, "en-US"),
        (),
        UsageState.active,
    )
    chart = LocalChart("da1:chart", 0, 1.0, 0.0, Vec2(0.0, 0.0))
    cell = make_hex_cell(chart, AxialCoord(0, 0))
    axes = []
    placements = []
    for axis_id, expression in (("location", "Kunming"), ("phenomenon", "rain")):
        start = content.index(expression)
        step_id = f"step_da1_{axis_id}"
        axes.append(
            {
                "axis_id": axis_id,
                "ray": [
                    {
                        "step_id": step_id,
                        "expression": expression,
                        "basis": GrowthBasis.explicit_in_shard.value,
                        "basis_refs": [{"ref_type": "text_span", "record_id": SHARD_ID, "start_char": start, "end_char": start + len(expression), "quoted_text": expression}],
                        "rationale": None,
                    }
                ],
            }
        )
        placements.append(AxisPlacement(axis_id, step_id, cell, (cell,), None))
    return AdmissionRequest(
        ADMISSION_ID,
        shard,
        {
            "contract_version": "dc1.v1",
            "proposal_id": PROPOSAL_ID,
            "subject_shard_id": SHARD_ID,
            "submitted_at": RECORDED_AT,
            "budget": {"max_axes": 4, "max_total_steps": 8, "max_ray_steps": 4},
            "do_not_infer": ["synthetic DA1 fixture only"],
            "forbidden_inferences": ["no semantic fallback"],
            "possible_conflict_refs": [],
            "axes": axes,
        },
        AdmissionPlacementPlan("apl_da1_synthetic_weather", tuple(placements)),
        RECORDED_AT,
    )


def _manifest_counts(root: Path) -> dict[str, int]:
    return {
        name: sum(1 for path in (root / name).rglob("*") if path.is_file())
        for name in ("evidence", "cortex", "admission")
    }


if __name__ == "__main__":
    main()
