from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]


def test_agents_records_v38_hard_constraints() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for constraint in (
        "Adjacent physical-layer rotation is exactly 22.5 degrees",
        "beta = 2^(1/4)",
        "adjacent-layer density ratio is `sqrt(2)`",
        "Physical Memory Layer and Aggregation Order are separate identity domains",
        "OpenClaw selects exactly one final physical entry",
        "Use at least two independent Oracles",
    ):
        assert constraint in text
