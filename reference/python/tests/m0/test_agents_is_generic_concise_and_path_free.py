from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[4]


def test_agents_is_generic_concise_and_path_free() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 15
    assert "NOLLM_" not in text
    assert re.search(r"\b20\d{6}\b", text) is None
    for project_detail in ("Core", "Access", "OpenClaw", "current task", "current stage", "HEAD", "callback", "capability"):
        assert project_detail not in text
