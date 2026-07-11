from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]


def test_agents_is_generic_and_concise() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 20
    for stale_detail in ("callback fence", "client lease", "HandleBinding", "CORE +", "Current stage", "OpenClaw"):
        assert stale_detail not in text
    assert "current task" in text
    assert "clean working tree" in text
    assert "Git bundle" in text
