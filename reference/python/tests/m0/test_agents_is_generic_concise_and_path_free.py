from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[4]


def test_agents_records_v37_hard_constraints_concisely() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 15
    assert re.search(r"\b20\d{6}\b", text) is None
    for constraint in (
        "delta theta is 22.5 degrees",
        "beta is 2^(1/4)",
        "beta squared, or sqrt(2)",
        "Physical Memory Layer and Aggregation Order are different domains",
        "selects one final entry per traversal",
    ):
        assert constraint in text
