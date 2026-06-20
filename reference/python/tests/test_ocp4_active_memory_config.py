from __future__ import annotations

from pathlib import Path

from nollm.openclaw_active_memory_config import (
    OCP4_ACTIVE_MEMORY_PROMPT_APPEND,
    OCP4_ACTIVE_MEMORY_TOOLS,
    OCP4_AGENT_ID,
    build_ocp4_active_memory_patch,
)


def test_ocp4_active_memory_patch_is_controlled_and_read_only(tmp_path: Path) -> None:
    patch = build_ocp4_active_memory_patch(
        config_before={"agents": {"list": [{"id": "main"}]}},
        repo_root=tmp_path / "repo",
        workspace_root=tmp_path / "workspace",
        transcript_dir="out/nollm_runtime/ocp4/transcripts",
    )

    agents = patch["agents"]["list"]
    assert [agent["id"] for agent in agents] == ["main", OCP4_AGENT_ID]
    controlled = agents[-1]
    assert controlled["contextInjection"] == "never"
    assert "read" in controlled["tools"]["deny"]
    assert "nollm_memory_write_candidate" not in controlled["tools"]["alsoAllow"]
    assert "nollm_memory_commit_candidate" not in controlled["tools"]["alsoAllow"]

    active = patch["plugins"]["entries"]["active-memory"]["config"]
    assert active["agents"] == [OCP4_AGENT_ID]
    assert active["allowedChatTypes"] == ["direct"]
    assert active["persistTranscripts"] is True
    assert active["logging"] is True
    assert active["toolsAllow"] == OCP4_ACTIVE_MEMORY_TOOLS
    assert "nollm_memory_write_candidate" not in active["toolsAllow"]
    assert "nollm_memory_commit_candidate" not in active["toolsAllow"]
    assert active["promptAppend"] == OCP4_ACTIVE_MEMORY_PROMPT_APPEND


def test_ocp4_active_memory_patch_replaces_existing_controlled_agent(tmp_path: Path) -> None:
    patch = build_ocp4_active_memory_patch(
        config_before={"agents": {"list": [{"id": "main"}, {"id": OCP4_AGENT_ID, "workspace": "old"}]}},
        repo_root=tmp_path / "repo",
        workspace_root=tmp_path / "workspace",
    )

    agents = [agent for agent in patch["agents"]["list"] if agent["id"] == OCP4_AGENT_ID]

    assert len(agents) == 1
    assert agents[0]["workspace"] == str(tmp_path / "workspace")
