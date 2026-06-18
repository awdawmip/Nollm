from __future__ import annotations

import unittest

from nollm.geometry_profiles import GeometryProfile, get_geometry_profile
from nollm.reverse_cover import (
    ReverseCoverCase,
    build_incidence_problem,
    default_reverse_cover_cases,
    greedy_reverse_cover,
    nontrivial_reverse_cover_cases,
    normalize_solver_status,
    reverse_cover_report,
    reverse_cover_cases_for_pack,
    solve_lp_lower_bound,
    solve_milp_reverse_cover,
    validate_reverse_cover_report,
)


class ReverseCoverTests(unittest.TestCase):
    def test_case_id_is_deterministic_and_includes_center_offsets(self) -> None:
        case = ReverseCoverCase(step=4, target_radius=3, center_q=-2, center_r=1, case_pack="nontrivial")

        self.assertEqual(case.case_id, "nontrivial_step_4_radius_3_center_-2_1")
        self.assertEqual(case, ReverseCoverCase(step=4, target_radius=3, center_q=-2, center_r=1, case_pack="nontrivial"))

    def test_incidence_rows_cover_every_target_in_deterministic_cases(self) -> None:
        for profile_id in ("default_dream", "medium_practical"):
            profile = get_geometry_profile(profile_id)
            for case in default_reverse_cover_cases():
                with self.subTest(profile_id=profile_id, case_id=case.case_id):
                    problem = build_incidence_problem(profile, case)
                    self.assertEqual(len(problem.targets), 7)
                    self.assertTrue(all(row for row in problem.rows))

    def test_smoke_pack_still_uses_centered_radius_one_cases(self) -> None:
        cases = reverse_cover_cases_for_pack("smoke")

        self.assertEqual(cases, default_reverse_cover_cases())
        self.assertEqual([case.step for case in cases], [1, 2, 4, 8])
        self.assertTrue(all(case.target_radius == 1 for case in cases))
        self.assertTrue(all((case.center_q, case.center_r, case.case_pack) == (0, 0, "smoke") for case in cases))

    def test_nontrivial_pack_contains_radius_sweep_and_boundary_offsets(self) -> None:
        cases = nontrivial_reverse_cover_cases()
        centers = {(case.center_q, case.center_r) for case in cases if case.target_radius == 2 and case.step == 1}

        self.assertGreaterEqual(len(cases), 36)
        self.assertTrue({2, 3, 4}.issubset({case.target_radius for case in cases}))
        self.assertTrue({1, 2, 4, 8}.issubset({case.step for case in cases}))
        self.assertGreaterEqual(len(centers), 24)
        self.assertTrue(all(case.case_pack == "nontrivial" for case in cases))

    def test_greedy_result_is_feasible_when_targets_are_covered(self) -> None:
        problem = build_incidence_problem(get_geometry_profile("default_dream"), ReverseCoverCase(step=1))

        result = greedy_reverse_cover(problem)

        self.assertEqual(result["status"], "feasible")
        self.assertGreater(result["selected_count"], 0)
        self.assertEqual(len(result["selected_sources"]), result["selected_count"])

    def test_milp_status_controls_gap_emission(self) -> None:
        report = reverse_cover_report(profile_ids=["default_dream"], cases=[ReverseCoverCase(step=1)])
        case = report["profiles"][0]["cases"][0]  # type: ignore[index]

        if case["milp"]["status"] == "OPTIMAL":
            self.assertIn("gap", case)
            self.assertIn("objective", case["milp"])
        else:
            self.assertNotIn("gap", case)
            self.assertNotIn("opt", case)
            self.assertNotIn("opt", case["milp"])

    def test_timeout_or_nonoptimal_status_is_not_called_opt(self) -> None:
        self.assertEqual(normalize_solver_status(1), "FEASIBLE_OR_LIMITED")
        self.assertNotEqual(normalize_solver_status(1), "OPTIMAL")

        report = reverse_cover_report(profile_ids=["default_dream"], cases=[ReverseCoverCase(step=1)])
        case = report["profiles"][0]["cases"][0]  # type: ignore[index]
        if case["milp"]["status"] == "FEASIBLE_OR_LIMITED":
            self.assertIn("incumbent", case["milp"])
            self.assertNotIn("opt", case["milp"])

    def test_lp_lower_bound_and_capacity_do_not_exceed_proven_optimum(self) -> None:
        problem = build_incidence_problem(get_geometry_profile("medium_practical"), ReverseCoverCase(step=1))
        milp = solve_milp_reverse_cover(problem)
        lp = solve_lp_lower_bound(problem)
        report = reverse_cover_report(profile_ids=["medium_practical"], cases=[ReverseCoverCase(step=1)])
        case = report["profiles"][0]["cases"][0]  # type: ignore[index]

        if milp["status"] == "OPTIMAL":
            optimum = float(milp["objective"])
            if lp["status"] == "OPTIMAL":
                self.assertLessEqual(float(lp["objective"]), optimum + 1e-9)
            self.assertLessEqual(float(case["lower_bounds"]["capacity"]), optimum)

    def test_nontrivial_pack_has_nontrivial_optimum_when_solver_is_available(self) -> None:
        report = reverse_cover_report(
            profile_ids=["default_dream"],
            cases=nontrivial_reverse_cover_cases(),
        )
        cases = report["profiles"][0]["cases"]  # type: ignore[index]
        optimal_cases = [case for case in cases if case["milp"]["status"] == "OPTIMAL"]

        if optimal_cases:
            self.assertTrue(any(float(case["milp"]["objective"]) > 1.0 for case in optimal_cases))

    def test_pack_summary_counts_only_optimal_gaps(self) -> None:
        report = reverse_cover_report(
            profile_ids=["default_dream"],
            cases=[
                ReverseCoverCase(step=1),
                ReverseCoverCase(step=1, target_radius=2, case_pack="nontrivial"),
            ],
        )

        for summary in (report["case_pack_summary"], report["profiles"][0]["case_pack_summary"]):  # type: ignore[index]
            for item in summary.values():
                if item["optimal_case_count"] == 0:
                    self.assertIsNone(item["mean_gap"])
                    self.assertIsNone(item["max_gap"])
                else:
                    self.assertLessEqual(item["greedy_equal_opt_count"], item["optimal_case_count"])
                    self.assertLessEqual(item["greedy_nonoptimal_count"], item["optimal_case_count"])

    def test_report_is_json_safe_and_has_required_fields(self) -> None:
        report = reverse_cover_report(profile_ids=["default_dream", "medium_practical"], cases=[ReverseCoverCase(step=1)])

        validate_reverse_cover_report(report)
        self.assertEqual(report["schema"], "nollm.reverse_cover.v1")
        self.assertEqual(report["status"], "experimental_internal_only")
        self.assertIn("case_pack_summary", report)
        self.assertIn("comparison", report)
        self.assertIn("nontrivial", report["comparison"]["default_dream_vs_medium_practical"])
        for profile in report["profiles"]:
            self.assertIn("case_pack_summary", profile)
            case = profile["cases"][0]
            self.assertIn("case_pack", case)
            self.assertIn("target_cluster", case)
            self.assertIn("greedy", case)
            self.assertIn("milp", case)
            self.assertIn("lp_lower_bound", case)
            self.assertIn("lower_bounds", case)

    def test_report_fields_do_not_use_forbidden_semantics(self) -> None:
        report = reverse_cover_report(profile_ids=["default_dream"], cases=[ReverseCoverCase(step=1)])
        forbidden = {"parent", "children", "folder", "owner", "belongs_to"}

        self.assertTrue(forbidden.isdisjoint(_collect_keys(report)))

    def test_unsupported_geometry_is_rejected(self) -> None:
        unsupported = GeometryProfile(
            profile_id="unsupported",
            beta=2.0,
            theta_deg=0.0,
            role="benchmark",
            tiling_model="O",
            orientation="pointy",
            description="unsupported reverse-cover model",
        )

        with self.assertRaises(ValueError):
            build_incidence_problem(unsupported, ReverseCoverCase(step=1))

    def test_invalid_inputs_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ReverseCoverCase(step=0)
        with self.assertRaises(ValueError):
            ReverseCoverCase(step=1, target_radius=-1)
        with self.assertRaises(ValueError):
            ReverseCoverCase(step=1, center_q=1.5)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            reverse_cover_cases_for_pack("unknown")
        with self.assertRaises(ValueError):
            reverse_cover_report(time_limit_seconds=0)


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
