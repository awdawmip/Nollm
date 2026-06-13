from __future__ import annotations

from math import sqrt

DENSITY_RATIO = sqrt(2)
SIDE_LENGTH_RATIO = 2 ** (-1 / 4)
AREA_RATIO = 2 ** (-1 / 2)
ROTATION_STEP_DEGREES = 22.5
ROTATION_PERIOD_DEGREES = 60.0


def layer_rotation_degrees(layer: int) -> float:
    require_non_negative_layer(layer)
    return float((layer * ROTATION_STEP_DEGREES) % ROTATION_PERIOD_DEGREES)


def layer_scale(layer: int, base_scale: float = 1.0) -> float:
    require_non_negative_layer(layer)
    return float(base_scale * (2 ** (-layer / 4)))


def layer_area_ratio(layer: int) -> float:
    require_non_negative_layer(layer)
    return float(2 ** (-layer / 2))


def expected_hex_metadata(layer: int, base_scale: float = 1.0) -> dict:
    return {
        "rotation": layer_rotation_degrees(layer),
        "scale": layer_scale(layer, base_scale),
    }


def require_non_negative_layer(layer: int) -> None:
    if not isinstance(layer, int) or isinstance(layer, bool) or layer < 0:
        raise ValueError(f"layer must be a non-negative integer: {layer}")
