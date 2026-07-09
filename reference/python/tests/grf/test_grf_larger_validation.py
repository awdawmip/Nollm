from __future__ import annotations

from pathlib import Path

from nollm.grf.validation_bench import load_jsonl


ROOT = Path(__file__).resolve().parents[4]
DATASET_ROOT = ROOT / "experiments" / "grf" / "datasets"


def test_larger_validation_dataset_counts_and_false_friend_families() -> None:
    concentrated = load_jsonl(DATASET_ROOT / "concentrated_facts.jsonl")
    scattered = load_jsonl(DATASET_ROOT / "scattered_facts.jsonl")
    false_decoys = load_jsonl(DATASET_ROOT / "false_stitch_decoys.jsonl")
    groups = {item.group for item in false_decoys}

    assert len(concentrated) >= 60
    assert len(scattered) >= 80
    assert len(false_decoys) >= 60
    assert len(concentrated) + len(scattered) + len(false_decoys) >= 200
    assert {"apple_company", "apple_fruit", "java_language", "java_island", "java_coffee", "mercury_planet", "mercury_element", "mercury_messenger"} <= groups
    assert {"opposite_hot", "opposite_cold", "opposite_allow", "opposite_deny", "opposite_increase", "opposite_decrease"} <= groups
