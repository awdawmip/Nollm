from __future__ import annotations

import unittest

from nollm.geometry_profiles import GeometryProfile, get_geometry_profile
from nollm.multi_step_coverage import multi_step_coverage_report
from nollm.offset_sampling import (
    OffsetSample,
    deterministic_offset_samples,
    offset_samples,
    offset_sampling_report,
    offset_world_translation,
    seeded_random_offset_samples,
    validate_offset_sampling_report,
)


class OffsetSamplingTests(unittest.TestCase):
    def test_offset_sample_generation_is_deterministic(self) -> None:
        first = offset_samples(seed=20260616, random_count=4)
        second = offset_samples(seed=20260616, random_count=4)

        self.assertEqual(first, second)
        self.assertEqual(first[:2], (OffsetSample("center", 0.0, 0.0), OffsetSample("q_quarter", 0.25, 0.0)))
        self.assertEqual(len(first), len(deterministic_offset_samples()) + 4)
        self.assertNotEqual(
            seeded_random_offset_samples(seed=20260616, sample_count=2),
            seeded_random_offset_samples(seed=20260617, sample_count=2),
        )

    def test_world_offset_from_uv_basis_is_deterministic(self) -> None:
        profile = get_geometry_profile("default_dream")
        sample = OffsetSample("custom", 0.25, -0.5)

        self.assertEqual(
            offset_world_translation(profile, 2, sample),
            offset_world_translation(profile, 2, sample),
        )
        self.assertEqual(offset_world_translation(profile, 2, OffsetSample("center", 0.0, 0.0)), (0.0, 0.0))

    def test_center_offset_reproduces_g3_one_step_templates(self) -> None:
        report = offset_sampling_report(
            profile_ids=["default_dream", "medium_practical"],
            max_step=1,
            random_count=0,
        )

        for profile in report["profiles"]:
            with self.subTest(profile_id=profile["profile_id"]):
                sample = _sample_by_id(profile["steps"][0], "center")  # type: ignore[index]
                g3_step = _step_by_number(multi_step_coverage_report(profile["profile_id"], max_step=1), 1)  # type: ignore[index]
                self.assertEqual(sample["coverage_count"], g3_step["coverage_count"])
                self.assertAlmostEqual(sample["source_share_sum"], g3_step["source_share_sum"])
                self.assertAlmostEqual(sample["participation_ratio"], g3_step["participation_ratio"])
                self.assertEqual(sample["exact_containment_count"], g3_step["exact_containment_count"])
                self.assertEqual(sample["boundary_ambiguity_count"], g3_step["boundary_ambiguity_count"])

    def test_source_share_sum_remains_one_for_valid_samples(self) -> None:
        report = offset_sampling_report(
            profile_ids=["default_dream", "medium_practical"],
            max_step=3,
            random_count=3,
        )

        for profile in report["profiles"]:
            for step in profile["steps"]:
                for sample in step["samples"]:
                    with self.subTest(profile_id=profile["profile_id"], step=step["step"], sample_id=sample["sample_id"]):
                        self.assertAlmostEqual(sample["source_share_sum"], 1.0)

    def test_aggregate_variance_is_deterministic_and_nonnegative(self) -> None:
        first = offset_sampling_report(profile_ids=["default_dream"], max_step=2, random_count=4)
        second = offset_sampling_report(profile_ids=["default_dream"], max_step=2, random_count=4)

        self.assertEqual(first, second)
        for step in first["profiles"][0]["steps"]:  # type: ignore[index]
            aggregates = step["aggregates"]
            self.assertGreaterEqual(aggregates["coverage_count_variance"], 0.0)
            self.assertGreaterEqual(aggregates["participation_ratio_variance"], 0.0)
            self.assertGreaterEqual(aggregates["entropy_variance"], 0.0)
            self.assertGreaterEqual(aggregates["exact_containment_count_variance"], 0.0)

    def test_report_json_schema_has_required_fields(self) -> None:
        report = offset_sampling_report(max_step=1, random_count=1)

        validate_offset_sampling_report(report)
        self.assertEqual(report["schema"], "nollm.offset_sampling.v1")
        self.assertEqual(report["status"], "experimental_internal_only")
        self.assertIn("comparison", report)
        for profile in report["profiles"]:
            self.assertIn("profile_id", profile)
            self.assertIn("steps", profile)
            step = profile["steps"][0]
            self.assertEqual(step["sample_count"], 10)
            self.assertIn("aggregates", step)
            self.assertIn("samples", step)

    def test_unsupported_geometry_is_rejected(self) -> None:
        unsupported = GeometryProfile(
            profile_id="unsupported",
            beta=2.0,
            theta_deg=0.0,
            role="benchmark",
            tiling_model="O",
            orientation="pointy",
            description="unsupported offset sampling model",
        )

        with self.assertRaises(ValueError):
            offset_world_translation(unsupported, 1, OffsetSample("center", 0.0, 0.0))

    def test_report_fields_do_not_use_forbidden_semantics(self) -> None:
        report = offset_sampling_report(max_step=1, random_count=1)
        forbidden = {"parent", "children", "folder", "owner", "belongs_to"}

        self.assertTrue(forbidden.isdisjoint(_collect_keys(report)))

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            offset_sampling_report(max_step=0)
        with self.assertRaises(ValueError):
            offset_samples(random_count=-1)
        with self.assertRaises(ValueError):
            OffsetSample("", 0.0, 0.0)


def _step_by_number(report: dict[str, object], step_number: int) -> dict[str, object]:
    for step in report["steps"]:  # type: ignore[index]
        if step["step"] == step_number:
            return step
    raise AssertionError(f"missing step: {step_number}")


def _sample_by_id(step: dict[str, object], sample_id: str) -> dict[str, object]:
    for sample in step["samples"]:  # type: ignore[index]
        if sample["sample_id"] == sample_id:
            return sample
    raise AssertionError(f"missing sample: {sample_id}")


def _collect_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for item in value.values():
            keys.update(_collect_keys(item))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys.update(_collect_keys(item))
        return keys
    return set()


if __name__ == "__main__":
    unittest.main()
