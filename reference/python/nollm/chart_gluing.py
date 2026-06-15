from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable, Mapping

from nollm.geometry import (
    Coverage,
    Denominator,
    HexAddress,
    LayerSpec,
    SimilarityTransform,
    coverage_weight,
)


@dataclass(frozen=True)
class LocalChartSpec:
    chart_id: str
    seed: HexAddress
    source_radius: int
    layer_ids: tuple[int, ...]
    parameter_signature: str

    def __post_init__(self) -> None:
        _require_non_empty_string(self.chart_id, "chart_id")
        if not isinstance(self.seed, HexAddress):
            raise ValueError("seed must be a HexAddress")
        _require_non_negative_int(self.source_radius, "source_radius")
        if not isinstance(self.layer_ids, tuple) or not self.layer_ids:
            raise ValueError("layer_ids must be a non-empty tuple")
        for layer_id in self.layer_ids:
            _require_non_negative_int(layer_id, "layer_id")
        _require_non_empty_string(self.parameter_signature, "parameter_signature")


@dataclass(frozen=True)
class CandidateChartOverlap:
    source_chart_id: str
    target_chart_id: str
    overlap_rows: tuple[Coverage, ...]
    coverage_denominator: Denominator
    coverage_sum: float

    def __post_init__(self) -> None:
        _require_non_empty_string(self.source_chart_id, "source_chart_id")
        _require_non_empty_string(self.target_chart_id, "target_chart_id")
        _require_coverage_rows(self.overlap_rows)
        _require_denominator(self.coverage_denominator)
        _require_non_negative_number(self.coverage_sum, "coverage_sum")


@dataclass(frozen=True)
class GluingProposal:
    proposal_id: str
    source_chart_id: str
    target_chart_id: str
    similarity_candidate: SimilarityTransform
    residual: float
    evidence_rows: tuple[Coverage, ...]
    status: str = "candidate"

    def __post_init__(self) -> None:
        _require_non_empty_string(self.proposal_id, "proposal_id")
        _require_non_empty_string(self.source_chart_id, "source_chart_id")
        _require_non_empty_string(self.target_chart_id, "target_chart_id")
        if not isinstance(self.similarity_candidate, SimilarityTransform):
            raise ValueError("similarity_candidate must be a SimilarityTransform")
        _require_non_negative_number(self.residual, "residual")
        _require_coverage_rows(self.evidence_rows)
        _require_non_empty_string(self.status, "status")


def summarize_chart_overlap(
    source_chart_id: str,
    target_chart_id: str,
    overlap_rows: Iterable[Coverage],
    denominator: Denominator = "source",
) -> CandidateChartOverlap:
    _require_denominator(denominator)
    rows = tuple(overlap_rows)
    coverage_sum = sum(coverage_weight(row, denominator) for row in rows)
    return CandidateChartOverlap(
        source_chart_id=source_chart_id,
        target_chart_id=target_chart_id,
        overlap_rows=rows,
        coverage_denominator=denominator,
        coverage_sum=coverage_sum,
    )


def parameter_signature(layer_specs: Mapping[int, LayerSpec]) -> str:
    if not layer_specs:
        raise ValueError("layer_specs must be a non-empty mapping")

    rows = []
    for layer_id, spec in sorted(layer_specs.items(), key=lambda item: item[0]):
        _require_non_negative_int(layer_id, "layer_id")
        if not isinstance(spec, LayerSpec):
            raise ValueError("layer_specs values must be LayerSpec instances")
        if layer_id != spec.layer:
            raise ValueError("layer_specs keys must match LayerSpec.layer")
        rows.append(
            {
                "layer": spec.layer,
                "s0": spec.s0,
                "beta": spec.beta,
                "theta_deg": spec.theta_deg,
                "origin": list(spec.origin),
                "translation": list(spec.translation),
                "finer_down": spec.finer_down,
                "rotation_mod_deg": spec.rotation_mod_deg,
                "side_length": spec.side_length,
                "rotation_deg": spec.rotation_deg,
            }
        )

    return json.dumps({"layers": rows}, sort_keys=True, separators=(",", ":"))


def _require_non_empty_string(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


def _require_non_negative_int(value: int, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")


def _require_non_negative_number(value: float, label: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative number")


def _require_denominator(value: Denominator) -> None:
    if value not in ("source", "target", "union"):
        raise ValueError(f"unsupported denominator: {value}")


def _require_coverage_rows(rows: tuple[Coverage, ...]) -> None:
    if not isinstance(rows, tuple):
        raise ValueError("coverage rows must be a tuple")
    for row in rows:
        if not isinstance(row, Coverage):
            raise ValueError("coverage rows must contain Coverage instances")


__all__ = [
    "LocalChartSpec",
    "CandidateChartOverlap",
    "GluingProposal",
    "summarize_chart_overlap",
    "parameter_signature",
]
