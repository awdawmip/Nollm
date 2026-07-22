import json
from pathlib import Path


def test_rev5_input_counterexamples_are_complete_and_bound_to_input_head() -> None:
    root = Path(__file__).resolve().parents[3]
    value = json.loads((root / "validation" / "aold_rev5_input_counterexamples_20260722.json").read_text(encoding="utf-8"))
    assert value["schema_version"] == "nollm_aold_rev5_input_counterexamples_v1"
    assert value["input_head"] == "a4d8e3135ef894453e1d01dc5c19139d23d9c71f"
    observations = {item["id"]: item for item in value["observations"]}
    assert set(observations) == {
        "legacy-wrong-date",
        "mismatched-reference-basis",
        "stale-cartography-apply",
        "llm-offset-index-failures",
        "hidden-reader-latency",
        "locality-over-injection",
    }
    assert all(item["observed"] is True for item in observations.values())
    assert observations["llm-offset-index-failures"]["attempts"] == 31
    assert max(observations["hidden-reader-latency"]["latency_ms"]) == 33700
    assert observations["locality-over-injection"]["statement_counts"] == [7, 6, 6, 7]
