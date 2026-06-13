from __future__ import annotations

import unittest

from nollm.honeycomb import (
    AREA_RATIO,
    DENSITY_RATIO,
    ROTATION_STEP_DEGREES,
    SIDE_LENGTH_RATIO,
    expected_hex_metadata,
    layer_area_ratio,
    layer_rotation_degrees,
    layer_scale,
)


class HoneycombHelperTests(unittest.TestCase):
    def test_layer_rotations_are_deterministic(self) -> None:
        expected = [0.0, 22.5, 45.0, 7.5, 30.0, 52.5, 15.0, 37.5, 0.0]
        self.assertEqual([layer_rotation_degrees(layer) for layer in range(9)], expected)

    def test_layer_scale_ratios(self) -> None:
        for layer in range(5):
            self.assertAlmostEqual(layer_scale(layer), 2 ** (-layer / 4))
        self.assertAlmostEqual(layer_scale(1), SIDE_LENGTH_RATIO)

    def test_layer_area_ratios(self) -> None:
        for layer in range(5):
            self.assertAlmostEqual(layer_area_ratio(layer), 2 ** (-layer / 2))
        self.assertAlmostEqual(layer_area_ratio(1), AREA_RATIO)

    def test_expected_hex_metadata_is_pure_and_deterministic(self) -> None:
        first = expected_hex_metadata(2)
        second = expected_hex_metadata(2)
        self.assertEqual(first, second)
        self.assertEqual(first["rotation"], 45.0)
        self.assertAlmostEqual(first["scale"], 2 ** (-2 / 4))

    def test_constants_match_architecture_contract(self) -> None:
        self.assertAlmostEqual(DENSITY_RATIO, 2 ** 0.5)
        self.assertEqual(ROTATION_STEP_DEGREES, 22.5)

    def test_negative_or_non_integer_layer_is_rejected(self) -> None:
        for layer in (-1, 1.5, "1", None, True):
            with self.assertRaises(ValueError):
                layer_rotation_degrees(layer)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
