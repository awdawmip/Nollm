from __future__ import annotations

import unittest

from nollm.geometry import HexAddress
from nollm.scale_scan_traversal import (
    ScaleScanPlan,
    ScaleScanStep,
    make_linear_scale_scan_plan,
    scale_scan_plan_from_record,
    scale_scan_plan_to_record,
)


class ScaleScanTraversalTests(unittest.TestCase):
    def test_plan_round_trip(self) -> None:
        plan = make_linear_scale_scan_plan("shard-a", "chart-a", HexAddress(0, 0, 0), 2, 1)
        self.assertEqual(scale_scan_plan_from_record(scale_scan_plan_to_record(plan)), plan)

    def test_layers_are_non_negative_and_deterministic(self) -> None:
        plan = make_linear_scale_scan_plan("shard-a", "chart-a", HexAddress(1, 2, -1), 2, 0)
        self.assertEqual([step.layer for step in plan.steps], [1, 2, 3])
        self.assertTrue(all(len(step.addresses) == 1 for step in plan.steps))

    def test_validation_rejects_bad_bounds(self) -> None:
        with self.assertRaises(ValueError):
            make_linear_scale_scan_plan("shard-a", "chart-a", HexAddress(0, 0, 0), -1, 1)
        with self.assertRaises(ValueError):
            make_linear_scale_scan_plan("shard-a", "chart-a", HexAddress(0, 0, 0), 1, True)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            ScaleScanStep(-1, "chart-a", (HexAddress(0, 0, 0),), "reason")

    def test_no_parent_children_fields(self) -> None:
        plan = make_linear_scale_scan_plan("shard-a", "chart-a", HexAddress(0, 0, 0), 1, 1)
        self.assertEqual(plan.status, "candidate")
        for obj in (plan, plan.steps[0]):
            for name in ("parent", "children", "leaf", "tree"):
                self.assertFalse(hasattr(obj, name))

    def test_plan_rejects_unknown_status(self) -> None:
        step = ScaleScanStep(0, "chart-a", (HexAddress(0, 0, 0),), "reason")
        with self.assertRaises(ValueError):
            ScaleScanPlan("plan-a", "shard-a", (step,), "done", status="confirmed")


if __name__ == "__main__":
    unittest.main()
