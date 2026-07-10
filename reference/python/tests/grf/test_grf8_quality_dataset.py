from nollm.grf.grf8_quality_dataset import CATEGORIES, build_quality_dataset, dataset_digest


def test_quality_dataset_has_six_categories_and_deterministic_truth() -> None:
    first = build_quality_dataset(60, 60)
    second = build_quality_dataset(60, 60)
    assert {item.category for item in first[0]} == set(CATEGORIES)
    assert all(item.relevant_shard_ids and item.hard_negative_shard_ids for item in first[1])
    assert dataset_digest(*first) == dataset_digest(*second)
