"""Small GRF validation helpers used by tests and reports."""

from __future__ import annotations

from pathlib import Path

from .coverage_template import DEFAULT_FANOUT_LIMIT
from .fixed_point import WEIGHT_FORMAT
from .profiles import performance_profile


def validation_summary() -> dict[str, object]:
    return {
        "default_performance_profile": performance_profile().profile_id,
        "fanout_limit": DEFAULT_FANOUT_LIMIT,
        "weight_format": WEIGHT_FORMAT,
        "runtime_float_allowed": False,
        "runtime_polygon": False,
    }


def source_contains_forbidden_runtime_terms(source_root: Path) -> list[str]:
    forbidden = ["shapely", "polygon", "clip", "sin(", "cos(", "float("]
    offenders = []
    for path in source_root.rglob("*.py"):
        if path.name.startswith("test_"):
            continue
        text = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.name}:{token}")
    return sorted(offenders)
