from __future__ import annotations

from nollm.grf.scale_validation import SCALE_VALIDATION_SEED, generate_scale_validation_items


def test_scale_validation_generator_reaches_1000_and_new_false_friends() -> None:
    items = generate_scale_validation_items()
    groups = {item.group for item in items}

    assert SCALE_VALIDATION_SEED == "grf1lm_scale_seed_v1"
    assert len(items) >= 1000
    assert sum(1 for item in items if item.item_id.startswith("A")) >= 300
    assert sum(1 for item in items if item.item_id.startswith("B")) >= 400
    assert sum(1 for item in items if item.item_id.startswith("C")) >= 300
    assert {"python_language", "python_snake", "python_package", "saturn_planet", "saturn_car", "saturn_myth"} <= groups
