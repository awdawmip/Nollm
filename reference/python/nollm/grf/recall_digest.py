"""GRF recall result objects."""

from __future__ import annotations

from dataclasses import dataclass

from .cell_address import CellAddress


@dataclass(frozen=True)
class RecallPath:
    from_cell: CellAddress
    to_cell: CellAddress
    kernel_type: str
    weight_q16: int
    accumulated_score_q16: int
    step: int
    flags: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "from_cell": self.from_cell.to_mapping(),
            "to_cell": self.to_cell.to_mapping(),
            "kernel_type": self.kernel_type,
            "weight_q16": self.weight_q16,
            "accumulated_score_q16": self.accumulated_score_q16,
            "step": self.step,
            "flags": tuple(sorted(self.flags)),
            "path_is_not_proof": True,
        }


@dataclass(frozen=True)
class CoverageReport:
    entry: str
    result: str
    path: tuple[RecallPath, ...]
    accumulated_weight_q16: int
    drift: dict[str, int]
    coverage_class: str
    bridge_count: int
    source_fallback_ref: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "entry": self.entry,
            "result": self.result,
            "path": tuple(item.to_mapping() for item in self.path),
            "accumulated_weight_q16": self.accumulated_weight_q16,
            "drift": dict(sorted(self.drift.items())),
            "coverage_class": self.coverage_class,
            "bridge_count": self.bridge_count,
            "source_fallback_ref": self.source_fallback_ref,
        }


@dataclass(frozen=True)
class RecallDigest:
    query_id: str
    selected_shards: tuple[str, ...]
    coverage_reports: tuple[CoverageReport, ...]
    rejected_or_deprioritized: tuple[str, ...]
    budget_exhausted: bool
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.query_id, str) or self.query_id == "":
            raise ValueError("query_id must be non-empty text")
        selected = set(self.selected_shards)
        reported = {report.result for report in self.coverage_reports}
        if selected != reported:
            raise ValueError("every selected shard must have a coverage report")
        if any(report.source_fallback_ref == "" for report in self.coverage_reports):
            raise ValueError("every selected shard must have source_fallback_ref")

    def to_mapping(self) -> dict[str, object]:
        return {
            "query_id": self.query_id,
            "selected_shards": tuple(self.selected_shards),
            "coverage_reports": tuple(report.to_mapping() for report in self.coverage_reports),
            "rejected_or_deprioritized": tuple(self.rejected_or_deprioritized),
            "budget_exhausted": self.budget_exhausted,
            "warnings": tuple(self.warnings),
            "recall_miss_scope": "current_explicit_grf_workset",
            "not_fact_confirmation": True,
        }
