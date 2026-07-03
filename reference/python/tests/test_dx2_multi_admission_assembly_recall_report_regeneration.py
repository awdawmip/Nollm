from __future__ import annotations

import re

from validation.dx2.run_dx2_multi_admission_assembly_recall import build_report


def test_dx2_report_regenerates_to_committed_baseline() -> None:
    expected = _normalize(open("docs/validation/DX2_MULTI_ADMISSION_ASSEMBLY_RECALL_BASELINE_REPORT.md", encoding="utf-8").read())
    actual = _normalize(build_report())
    assert actual == expected


def _normalize(value: str) -> str:
    return re.sub(r"- validation_head: `[^`]+`", "- validation_head: `<normalized>`", value).strip()

