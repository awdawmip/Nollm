from __future__ import annotations

import argparse
import json
from decimal import Decimal

from compiler import CoverageTemplateCompiler
from physical_geometry import canonical_overlap


def validate() -> dict[str, object]:
    compiler = CoverageTemplateCompiler()
    phase_results = []
    for phase in range(8):
        for direction in ("coverage_up", "coverage_down"):
            template = compiler.compile("default_dream_v1", direction, phase)
            assert len(template.entries) == 7
            assert sum(entry.weight_q16 for entry in template.entries) == 65536
            for entry in template.entries:
                area, source_share, target_share = canonical_overlap(phase, direction, entry.dq, entry.dr)
                assert Decimal(entry.intersection_area_lower) <= area <= Decimal(entry.intersection_area_upper)
                assert abs(entry.source_share_q16 - int((source_share * 65536).to_integral_value(rounding="ROUND_HALF_EVEN"))) <= 1
                assert abs(entry.target_share_q16 - int((target_share * 65536).to_integral_value(rounding="ROUND_HALF_EVEN"))) <= 1
            phase_results.append({"phase": phase, "direction": direction, "fanout": len(template.entries), "residual_q16": template.approximation_residual_q16})
    return {"schema_version": "nollm_certified_coverage_validation_v1", "phase_results": phase_results}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args()
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
