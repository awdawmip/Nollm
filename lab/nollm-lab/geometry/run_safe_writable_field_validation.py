from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]

from nollm_access import (  # noqa: E402
    ACTIVE_SEMANTIC_WRITE_POLICY,
    ActiveSemanticWritePolicyError,
)
from nollm_core import (  # noqa: E402
    ACTIVE_APPROXIMATION_POLICY,
    GeometryAddress,
    expand_physical_coverage,
)


def _radius(address: GeometryAddress) -> int:
    return max(abs(address.q), abs(address.r), abs(address.q + address.r))


def validate() -> dict[str, object]:
    policy = ACTIVE_APPROXIMATION_POLICY
    radius = policy.active_writable_hex_radius
    corners = ((radius, 0), (0, radius), (-radius, radius), (-radius, 0), (0, -radius), (radius, -radius))
    first_step_count = second_step_count = 0
    maximum_required_radius = 0
    worst_case = None
    for phase in range(8):
        for q, r in corners:
            source = GeometryAddress("default_dream_v1", "default", phase, q, r)
            ACTIVE_SEMANTIC_WRITE_POLICY.validate(
                GeometryAddress("default_dream_v1", "default", 0, q, r)
            )
            for direction in ("coverage_up", "coverage_down"):
                first = expand_physical_coverage(source, direction)
                first_step_count += len(first.members)
                for member in first.members:
                    required = _radius(member.target)
                    if required > maximum_required_radius:
                        maximum_required_radius = required
                        worst_case = (phase, q, r, direction, 1, member.target.q, member.target.r)
            first_down = expand_physical_coverage(source, "coverage_down")
            for member in first_down.members:
                second = expand_physical_coverage(member.target, "coverage_down")
                second_step_count += len(second.members)
                for leaf in second.members:
                    required = _radius(leaf.target)
                    if required > maximum_required_radius:
                        maximum_required_radius = required
                        worst_case = (phase, q, r, "coverage_down", 2, leaf.target.q, leaf.target.r)

    rejected_radius = radius + 1
    rejected = GeometryAddress("default_dream_v1", "default", 0, rejected_radius, 0)
    try:
        ACTIVE_SEMANTIC_WRITE_POLICY.validate(rejected)
    except ActiveSemanticWritePolicyError as error:
        rejection = {
            "required_radius": error.actual,
            "active_writable_radius": policy.active_writable_hex_radius,
            "contract_id": error.contract_id,
        }
    else:
        rejection = None

    checks = {
        "six_boundary_directions": len(corners) == 6,
        "all_phases": True,
        "single_up_down_within_storage": maximum_required_radius <= policy.storage_hex_radius,
        "two_down_steps_within_storage": maximum_required_radius <= policy.storage_hex_radius,
        "positive_storage_margin": policy.storage_hex_radius - maximum_required_radius > 0,
        "unsafe_write_rejected": rejection is not None,
        "configured_depth": policy.max_coverage_down_steps == 2,
    }
    return {
        "schema_version": "nollm_safe_writable_field_validation_v1",
        "policy": {
            "contract_id": policy.writable_field_contract_id,
            "storage_hex_radius": policy.storage_hex_radius,
            "active_writable_hex_radius": policy.active_writable_hex_radius,
            "max_coverage_down_steps": policy.max_coverage_down_steps,
        },
        "source_fixture_count": 8 * len(corners),
        "first_step_member_count": first_step_count,
        "second_step_member_count": second_step_count,
        "maximum_required_radius": maximum_required_radius,
        "storage_margin": policy.storage_hex_radius - maximum_required_radius,
        "worst_case": worst_case,
        "rejection": rejection,
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
