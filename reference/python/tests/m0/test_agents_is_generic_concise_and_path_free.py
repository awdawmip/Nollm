from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]


def test_agents_records_v39_hard_constraints() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for constraint in (
        "Adjacent physical-layer rotation increment is 22.5 degrees",
        "beta = 2^(1/4)",
        "adjacent-layer density ratio is `sqrt(2)`",
        "Physical Memory Layer and Aggregation Order are separate identity domains",
        "One traversal selects one final physical entry",
        "Production Coverage is a bounded structural approximation",
        "Surface Orders are computed lazily",
    ):
        assert constraint in text
