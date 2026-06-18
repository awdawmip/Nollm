from __future__ import annotations

from math import sqrt
import unittest

from nollm.multi_step_coverage import (
    coverage_support,
    multi_profile_coverage_report,
    multi_step_coverage_report,
    validate_multi_profile_coverage_report,
)


class MultiStepCoverageTests(unittest.TestCase):
    def test_report_shape_is_json_safe_and_internal(self) -> None:
        report = multi_profile_coverage_report(max_step=2)

        validate_multi_profile_coverage_report(report)
        self.assertEqual(report["schema"], "nollm.multi_step_coverage.v1")
        self.assertEqual(report["status"], "experimental_internal_only")
        self.assertEqual(len(report["profiles"]), 5)

    def test_medium_practical_one_step_template_agrees_with_kernel(self) -> None:
        step = _step_by_number(multi_step_coverage_report("medium_practical", max_step=1), 1)
        center = _coverage_for(step, 0, 0)
        outer = [row for row in step["coverage"] if row != center]

        self.assertEqual(step["coverage_count"], 7)
        self.assertAlmostEqual(step["source_share_sum"], 1.0)
        self.assertAlmostEqual(center["source_share"], 0.5)
        self.assertTrue(all(_almost_equal(row["source_share"], 1.0 / 12.0) for row in outer))
        self.assertEqual(step["exact_containment_count"], 1)
        self.assertEqual(step["boundary_ambiguity_count"], 6)

    def test_default_dream_one_step_template_agrees_with_kernel(self) -> None:
        step = _step_by_number(multi_step_coverage_report("default_dream", max_step=1), 1)
        center = _coverage_for(step, 0, 0)
        outer = [row for row in step["coverage"] if row != center]

        self.assertEqual(step["coverage_count"], 7)
        self.assertAlmostEqual(step["source_share_sum"], 1.0)
        self.assertAlmostEqual(center["source_share"], 1.0 / sqrt(2))
        self.assertTrue(all(_almost_equal(row["source_share"], (2.0 - sqrt(2)) / 12.0) for row in outer))
        self.assertEqual(step["exact_containment_count"], 1)
        self.assertEqual(step["boundary_ambiguity_count"], 6)

    def test_multi_step_metrics_are_well_formed_for_n_1_to_8(self) -> None:
        report = multi_profile_coverage_report(profile_ids=["default_dream", "medium_practical"], max_step=8)

        for profile in report["profiles"]:
            for step in profile["steps"]:
                with self.subTest(profile_id=profile["profile_id"], step=step["step"]):
                    self.assertAlmostEqual(step["source_share_sum"], 1.0)
                    self.assertGreater(step["coverage_count"], 0)
                    self.assertGreater(step["participation_ratio"], 0.0)
                    self.assertGreaterEqual(step["entropy"], 0.0)
                    self.assertGreaterEqual(step["exact_containment_count"], 0)
                    for row in step["coverage"]:
                        self.assertGreater(row["source_share"], 0.0)
                        self.assertGreater(row["target_share"], 0.0)
                        self.assertLessEqual(row["target_share"], 1.0 + 1e-9)

    def test_default_dream_has_smaller_finite_depth_support_growth_than_medium_practical(self) -> None:
        default_step = _step_by_number(multi_step_coverage_report("default_dream", max_step=8), 8)
        medium_step = _step_by_number(multi_step_coverage_report("medium_practical", max_step=8), 8)

        self.assertLess(default_step["coverage_count"], medium_step["coverage_count"])
        self.assertEqual(default_step["coverage_count"], 19)
        self.assertEqual(medium_step["coverage_count"], 271)

    def test_coverage_support_is_sorted_and_uses_source_target_share_names(self) -> None:
        support = coverage_support("default_dream", 1)

        self.assertEqual(support, sorted(support, key=lambda row: (row["q"], row["r"])))
        self.assertTrue(all(set(row) == {"q", "r", "source_share", "target_share"} for row in support))
        self.assertNotEqual(
            [round(row["source_share"], 12) for row in support],
            [round(row["target_share"], 12) for row in support],
        )

    def test_invalid_step_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            multi_step_coverage_report("default_dream", max_step=0)
        with self.assertRaises(ValueError):
            coverage_support("default_dream", 0)


def _step_by_number(report: dict[str, object], step_number: int) -> dict[str, object]:
    for step in report["steps"]:  # type: ignore[index]
        if step["step"] == step_number:
            return step
    raise AssertionError(f"missing step: {step_number}")


def _coverage_for(step: dict[str, object], q: int, r: int) -> dict[str, object]:
    for row in step["coverage"]:  # type: ignore[index]
        if row["q"] == q and row["r"] == r:
            return row
    raise AssertionError(f"missing coverage row: {(q, r)}")


def _almost_equal(a: object, b: float, tolerance: float = 1e-9) -> bool:
    return abs(float(a) - b) <= tolerance


if __name__ == "__main__":
    unittest.main()
