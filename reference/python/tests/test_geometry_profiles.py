from __future__ import annotations

from math import inf, sqrt
import unittest

from nollm.geometry_profiles import (
    GeometryProfile,
    canonical_geometry_profiles,
    default_geometry_profile,
    geometry_profile_from_record,
    geometry_profile_registry,
    geometry_profile_to_record,
    get_geometry_profile,
    layer_spec_from_profile,
)


class GeometryProfileRegistryTests(unittest.TestCase):
    def test_canonical_registry_contains_exactly_required_profiles(self) -> None:
        profiles = canonical_geometry_profiles()

        self.assertEqual(
            [profile.profile_id for profile in profiles],
            [
                "default_dream",
                "medium_practical",
                "benchmark_aligned",
                "benchmark_single_step",
                "benchmark_eisenstein",
            ],
        )
        self.assertEqual(set(geometry_profile_registry()), {profile.profile_id for profile in profiles})

    def test_default_profile_is_default_dream_b_profile(self) -> None:
        profile = default_geometry_profile()

        self.assertEqual(profile.profile_id, "default_dream")
        self.assertEqual(profile.role, "default")
        self.assertAlmostEqual(profile.beta, 2 ** 0.25)
        self.assertAlmostEqual(profile.theta_deg, 22.5)
        self.assertEqual(profile.tiling_model, "T")
        self.assertEqual(profile.orientation, "pointy")
        self.assertIn("B default", profile.description)
        self.assertIn("delays finite-depth recurrence", profile.description)

    def test_medium_practical_is_secondary_a_profile(self) -> None:
        profile = get_geometry_profile("medium_practical")

        self.assertEqual(profile.role, "secondary")
        self.assertAlmostEqual(profile.beta, sqrt(2))
        self.assertAlmostEqual(profile.theta_deg, 15.0)
        self.assertIn("A secondary", profile.description)
        self.assertNotEqual(profile.role, "default")

    def test_benchmark_profiles_are_benchmark_only(self) -> None:
        registry = geometry_profile_registry()
        benchmark_ids = [
            "benchmark_aligned",
            "benchmark_single_step",
            "benchmark_eisenstein",
        ]

        for profile_id in benchmark_ids:
            with self.subTest(profile_id=profile_id):
                profile = registry[profile_id]
                self.assertEqual(profile.role, "benchmark")
                self.assertIn("not a default", profile.description)

    def test_no_profile_id_duplicates(self) -> None:
        profile_ids = [profile.profile_id for profile in canonical_geometry_profiles()]

        self.assertEqual(len(profile_ids), len(set(profile_ids)))

    def test_record_round_trip(self) -> None:
        for profile in canonical_geometry_profiles():
            with self.subTest(profile_id=profile.profile_id):
                self.assertEqual(
                    geometry_profile_from_record(geometry_profile_to_record(profile)),
                    profile,
                )

    def test_invalid_values_are_rejected(self) -> None:
        invalid_kwargs = [
            {"profile_id": ""},
            {"beta": 0.0},
            {"beta": inf},
            {"theta_deg": -1.0},
            {"theta_deg": inf},
            {"role": "primary"},
            {"tiling_model": "M"},
            {"orientation": "diagonal"},
            {"description": ""},
        ]
        base = {
            "profile_id": "x",
            "beta": 1.2,
            "theta_deg": 15.0,
            "role": "benchmark",
            "tiling_model": "T",
            "orientation": "pointy",
            "description": "valid profile",
        }
        for kwargs in invalid_kwargs:
            with self.subTest(kwargs=kwargs):
                data = dict(base)
                data.update(kwargs)
                with self.assertRaises(ValueError):
                    GeometryProfile(**data)  # type: ignore[arg-type]

    def test_unknown_profile_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            get_geometry_profile("missing")

    def test_layer_spec_from_profile_matches_geometry_kernel(self) -> None:
        profile = default_geometry_profile()
        layer = layer_spec_from_profile(
            profile,
            1,
            s0=2.0,
            origin=(1.0, 2.0),
            translation=(0.25, -0.5),
        )

        self.assertEqual(layer.layer, 1)
        self.assertAlmostEqual(layer.beta, 2 ** 0.25)
        self.assertAlmostEqual(layer.theta_deg, 22.5)
        self.assertEqual(layer.orientation, "pointy")
        self.assertAlmostEqual(layer.side_length, 2.0 * (2 ** 0.25) ** -1)
        self.assertAlmostEqual(layer.rotation_deg, 22.5)
        self.assertEqual(layer.origin, (1.0, 2.0))
        self.assertEqual(layer.translation, (0.25, -0.5))

    def test_layer_spec_rejects_non_model_t_profile(self) -> None:
        profile = GeometryProfile(
            profile_id="research_o",
            beta=1.2,
            theta_deg=15.0,
            role="benchmark",
            tiling_model="O",
            orientation="pointy",
            description="research-only overlapping model",
        )

        with self.assertRaises(ValueError):
            layer_spec_from_profile(profile, 0)

    def test_canonical_profiles_use_model_t_pointy(self) -> None:
        for profile in canonical_geometry_profiles():
            with self.subTest(profile_id=profile.profile_id):
                self.assertEqual(profile.tiling_model, "T")
                self.assertEqual(profile.orientation, "pointy")


if __name__ == "__main__":
    unittest.main()
