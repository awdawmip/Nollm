from __future__ import annotations

import math
import unittest

from nollm.gravity import (
    GravityMark,
    GravityReport,
    GravityWell,
    anchor_similarity,
    create_gravity_report,
    gravity_mark_from_record,
    gravity_mark_to_record,
    gravity_report_from_record,
    gravity_report_to_record,
    gravity_well_from_record,
    gravity_well_to_record,
    validate_gravity_report,
)


class GravityTests(unittest.TestCase):
    def test_gravity_well_and_mark_validation_rejects_invalid_records(self) -> None:
        with self.assertRaises(ValueError):
            _well(well_id="")
        with self.assertRaises(ValueError):
            _well(layer=-1)
        with self.assertRaises(ValueError):
            _well(q=1.5)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            _well(anchor_vector={"a": -0.1})
        with self.assertRaises(ValueError):
            _well(anchor_vector={"a": math.inf})
        with self.assertRaises(ValueError):
            _mark(content_id="")
        with self.assertRaises(ValueError):
            _mark(anchor_vector={"": 1.0})

    def test_anchor_similarity_is_deterministic_clamped_and_handles_zero_vectors(self) -> None:
        self.assertEqual(anchor_similarity({}, {"a": 1.0}), 0.0)
        self.assertEqual(anchor_similarity({"a": 0.0}, {"a": 1.0}), 0.0)
        self.assertEqual(anchor_similarity({"a": 1.0}, {"a": 1.0}), 1.0)
        self.assertAlmostEqual(anchor_similarity({"a": 1.0, "b": 1.0}, {"a": 1.0}), 1.0 / math.sqrt(2.0))
        self.assertEqual(
            anchor_similarity({"a": 0.2, "b": 0.8}, {"b": 0.3}),
            anchor_similarity({"b": 0.8, "a": 0.2}, {"b": 0.3}),
        )
        with self.assertRaises(ValueError):
            anchor_similarity({"a": -1.0}, {"a": 1.0})

    def test_same_layer_r_distance_and_classes(self) -> None:
        well = _well(anchor_vector={"a": 1.0})

        self.assertEqual(create_gravity_report(well, _mark(q=0, r=0, anchor_vector={"a": 1.0})).drift_class, "core")
        self.assertEqual(create_gravity_report(well, _mark(q=1, r=0, anchor_vector={"a": 1.0})).drift_class, "halo")
        self.assertEqual(create_gravity_report(well, _mark(q=4, r=0, anchor_vector={"a": 1.0})).drift_class, "far_coherent")
        self.assertEqual(create_gravity_report(well, _mark(q=4, r=0, anchor_vector={"a": 1.0, "b": 1.0})).drift_class, "far_weak")

    def test_semantic_break_overrides_core_and_halo(self) -> None:
        well = _well(anchor_vector={"a": 1.0})

        core_break = create_gravity_report(well, _mark(q=0, r=0, anchor_vector={"b": 1.0}))
        halo_break = create_gravity_report(well, _mark(q=1, r=0, anchor_vector={"b": 1.0}))

        self.assertEqual(core_break.drift_class, "semantic_break")
        self.assertEqual(halo_break.drift_class, "semantic_break")
        self.assertEqual(core_break.R_column_ring, 0)

    def test_near_drift_and_far_weak_rules(self) -> None:
        well = _well(anchor_vector={"a": 1.0})

        self.assertEqual(create_gravity_report(well, _mark(q=2, r=0, anchor_vector={"a": 1.0})).drift_class, "near_drift")
        self.assertEqual(create_gravity_report(well, _mark(q=3, r=0, anchor_vector={"a": 0.6, "b": 0.8})).drift_class, "near_drift")
        self.assertEqual(create_gravity_report(well, _mark(q=4, r=0, anchor_vector={"a": 0.7, "b": 0.7})).drift_class, "far_weak")

    def test_cross_chart_and_profile_mismatch_are_unavailable_without_fake_r(self) -> None:
        well = _well(anchor_vector={"a": 1.0})

        chart_report = create_gravity_report(well, _mark(chart_id="chart_beta", anchor_vector={"a": 1.0}))
        jump_report = create_gravity_report(
            well,
            _mark(chart_id="chart_beta", anchor_vector={"a": 1.0}),
            chart_relation_available=True,
        )
        profile_report = create_gravity_report(well, _mark(geometry_profile="medium_practical", anchor_vector={"a": 1.0}))

        self.assertIsNone(chart_report.R_column_ring)
        self.assertEqual(chart_report.projection_method, "unavailable")
        self.assertEqual(chart_report.drift_class, "unglued")
        self.assertEqual(jump_report.drift_class, "chart_jump")
        self.assertEqual(profile_report.drift_class, "unglued")

    def test_cross_layer_same_chart_profile_uses_coverage_template(self) -> None:
        report = create_gravity_report(
            _well(layer=0, anchor_vector={"a": 1.0}),
            _mark(layer=1, q=0, r=0, anchor_vector={"a": 1.0}),
        )

        self.assertEqual(report.projection_method, "coverage_template")
        self.assertEqual(report.R_column_ring, 0)
        self.assertEqual(report.S_scale_delta, 1)

    def test_record_round_trips_are_stable_and_json_primitive(self) -> None:
        well = _well(created_at="2026-06-18T00:00:00Z")
        mark = _mark(provenance="experiment")
        report = create_gravity_report(well, mark)

        self.assertEqual(gravity_well_from_record(gravity_well_to_record(well)), well)
        self.assertEqual(gravity_mark_from_record(gravity_mark_to_record(mark)), mark)
        self.assertEqual(gravity_report_from_record(gravity_report_to_record(report)), report)
        validate_gravity_report(gravity_report_to_record(report))

    def test_report_does_not_map_drift_class_to_trust_or_status(self) -> None:
        report = gravity_report_to_record(create_gravity_report(_well(), _mark()))

        self.assertIn("drift_class", report)
        self.assertEqual(report["status"], "experimental_internal_only")
        self.assertNotIn("trust", report)
        self.assertNotIn("memory_status", report)

    def test_invalid_report_null_ring_is_rejected_when_not_chart_jump_or_unglued(self) -> None:
        with self.assertRaises(ValueError):
            GravityReport(
                well_id="gw",
                content_id="content",
                geometry_profile="default_dream",
                well_chart_id="chart",
                content_chart_id="chart",
                R_column_ring=None,
                S_scale_delta=0,
                A_anchor_similarity=1.0,
                drift_class="core",
                projection_method="unavailable",
            )


def _well(**overrides: object) -> GravityWell:
    values = {
        "well_id": "gw_001",
        "entry_query": "entry",
        "geometry_profile": "default_dream",
        "chart_id": "chart_alpha",
        "layer": 0,
        "q": 0,
        "r": 0,
        "anchor_vector": {"a": 1.0},
        "created_at": None,
    }
    values.update(overrides)
    return GravityWell(**values)  # type: ignore[arg-type]


def _mark(**overrides: object) -> GravityMark:
    values = {
        "content_id": "content_001",
        "geometry_profile": "default_dream",
        "chart_id": "chart_alpha",
        "layer": 0,
        "q": 0,
        "r": 0,
        "anchor_vector": {"a": 1.0},
        "provenance": None,
    }
    values.update(overrides)
    return GravityMark(**values)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
