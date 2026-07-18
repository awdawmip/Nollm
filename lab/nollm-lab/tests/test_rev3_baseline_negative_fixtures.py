import json
from pathlib import Path


def test_rev3_baseline_records_all_five_input_counterexamples() -> None:
    root = Path(__file__).resolve().parents[3]
    value = json.loads((root / "validation" / "aold_prompt_bounded_cartography_baseline_20260718.json").read_text("utf-8"))

    assert value["input_head"] == "f9f01f56906c5ce64df4a4702f61d954a8402fb8"
    assert value["direct_target_reader_is_not_causal"] == {
        "provider_case_count": 10,
        "empty_target_path_count": 10,
        "relation_entry_proof": False,
    }
    assert value["stable_prefix_is_incomplete"]["q39_target_visible"] is False
    assert value["one_shot_prompt_is_unbounded"]["field_300_prompt_utf8_bytes"] > 65536
    assert value["one_shot_prompt_is_unbounded"]["field_1027_prompt_utf8_bytes"] > 65536
    assert value["independent_seed_is_blocked"]["resolved_lens_count"] == 0
    assert value["region_representatives_are_not_complete_context"]["representative_limit"] == 3
