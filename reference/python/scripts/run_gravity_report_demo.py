from __future__ import annotations

import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.gravity import (  # noqa: E402
    GravityMark,
    GravityWell,
    create_gravity_report,
    gravity_mark_to_record,
    gravity_report_to_record,
    gravity_well_to_record,
)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    output = repo_root / "out" / "nollm_runtime" / "gravity_report_demo.json"
    well = GravityWell(
        well_id="gw_demo",
        entry_query="demo entry",
        geometry_profile="default_dream",
        chart_id="chart_demo",
        layer=0,
        q=0,
        r=0,
        anchor_vector={"field.alpha": 1.0, "field.beta": 0.5},
        created_at="2026-06-18T00:00:00Z",
    )
    marks = [
        GravityMark(
            content_id="content_core",
            geometry_profile="default_dream",
            chart_id="chart_demo",
            layer=0,
            q=0,
            r=0,
            anchor_vector={"field.alpha": 1.0, "field.beta": 0.5},
            provenance="experiment",
        ),
        GravityMark(
            content_id="content_far",
            geometry_profile="default_dream",
            chart_id="chart_demo",
            layer=0,
            q=4,
            r=0,
            anchor_vector={"field.alpha": 0.9},
            provenance="experiment",
        ),
    ]
    reports = [create_gravity_report(well, mark) for mark in marks]
    payload = {
        "status": "experimental_internal_only",
        "gravity_well": gravity_well_to_record(well),
        "gravity_marks": [gravity_mark_to_record(mark) for mark in marks],
        "drift_reports": [gravity_report_to_record(report) for report in reports],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"wrote gravity report demo path={output} reports={len(reports)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
