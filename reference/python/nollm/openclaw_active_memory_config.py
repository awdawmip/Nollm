from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


OCP4_AGENT_ID = "ocp4-nollm-functional"
OCP4_ACTIVE_MEMORY_TOOLS = [
    "memory_search",
    "memory_get",
    "nollm_memory_recall",
    "nollm_memory_get",
]
OCP4_ACTIVE_MEMORY_PROMPT_APPEND = (
    "For memory-relevant user messages: "
    "1. Use nollm_memory_recall once. "
    "2. If direct evidence is present, verify the cited source with memory_get or nollm_memory_get. "
    "3. Return NONE when no relevant memory exists. "
    "4. Treat drift labels as orientation only; never reject a result solely because of drift."
)
DIRECT_TOOL_DENY = ["read", "exec", "process", "edit", "write", "apply_patch", "web_search", "web_fetch"]
OCP6R_AGENT_ID = "ocp6r-nollm-cortex"
OCP6R_CORTEX_TOOLS = [
    "nollm_orient",
    "nollm_surface",
    "nollm_focus",
    "nollm_drift",
    "nollm_read",
    "nollm_compose_digest",
]
OCP6R_CORTEX_PROMPT_APPEND = (
    "Act as Nollm Cortex, not as a raw memory searcher. "
    "For memory-relevant direct chat: 1. Use nollm_orient first and inspect coarse surface. "
    "2. Use nollm_surface before nollm_focus. "
    "3. Stop at sufficient scale; do not descend to raw source unless the user asks for source inspection. "
    "4. Use nollm_drift only for useful lateral context and label it lateral. "
    "5. Return to the entry task and call nollm_compose_digest. "
    "6. Return NONE when the dream field lacks useful material. "
    "Do not use memory_search or memory_get as the Nollm internal model."
)


def build_ocp4_active_memory_patch(
    *,
    config_before: Mapping[str, Any],
    repo_root: Path,
    workspace_root: Path,
    agent_id: str = OCP4_AGENT_ID,
    model: str = "kimi/kimi-for-coding",
    transcript_dir: str | None = None,
) -> dict[str, Any]:
    agents = _existing_agents(config_before)
    agents = [agent for agent in agents if agent.get("id") != agent_id]
    agents.append(
        {
            "id": agent_id,
            "name": agent_id,
            "workspace": str(workspace_root),
            "agentDir": str(Path.home() / ".openclaw" / "agents" / agent_id / "agent"),
            "model": model,
            "contextInjection": "never",
            "bootstrapMaxChars": 1,
            "bootstrapTotalMaxChars": 1,
            "memorySearch": {"provider": "none", "fallback": "none"},
            "tools": {
                "profile": "coding",
                "alsoAllow": OCP4_ACTIVE_MEMORY_TOOLS
                + [
                    "nollm_memory_search",
                    "nollm_memory_status",
                    "nollm_memory_write_candidate",
                    "nollm_memory_commit_candidate",
                ],
                "deny": DIRECT_TOOL_DENY,
            },
        }
    )
    active_config: dict[str, Any] = {
        "enabled": True,
        "agents": [agent_id],
        "allowedChatTypes": ["direct"],
        "queryMode": "message",
        "promptStyle": "precision-heavy",
        "toolsAllow": list(OCP4_ACTIVE_MEMORY_TOOLS),
        "promptAppend": OCP4_ACTIVE_MEMORY_PROMPT_APPEND,
        "logging": True,
        "persistTranscripts": True,
        "timeoutMs": 30000,
        "maxSummaryChars": 800,
        "recentUserTurns": 1,
        "recentAssistantTurns": 1,
    }
    if transcript_dir:
        active_config["transcriptDir"] = transcript_dir
    return {
        "agents": {"list": agents},
        "plugins": {
            "entries": {
                "active-memory": {
                    "enabled": True,
                    "config": active_config,
                },
                "nollm-memory-companion": {
                    "enabled": True,
                    "config": {
                        "pythonCommand": str(Path(sys.executable).resolve()),
                        "nollmRepoRoot": str(repo_root),
                        "workspaceRoot": str(workspace_root),
                        "sidecarOutDir": str(workspace_root / ".nollm-memory"),
                        "commandTimeoutMs": 15000,
                        "maxSearchResults": 6,
                    },
                },
            }
        },
    }


def build_ocp6r_cortex_active_memory_patch(
    *,
    config_before: Mapping[str, Any],
    repo_root: Path,
    workspace_root: Path,
    agent_id: str = OCP6R_AGENT_ID,
    model: str = "kimi/kimi-for-coding",
    transcript_dir: str | None = None,
) -> dict[str, Any]:
    agents = _existing_agents(config_before)
    agents = [agent for agent in agents if agent.get("id") != agent_id]
    agents.append(
        {
            "id": agent_id,
            "name": agent_id,
            "workspace": str(workspace_root),
            "agentDir": str(Path.home() / ".openclaw" / "agents" / agent_id / "agent"),
            "model": model,
            "contextInjection": "never",
            "bootstrapMaxChars": 1,
            "bootstrapTotalMaxChars": 1,
            "memorySearch": {"provider": "none", "fallback": "none"},
            "tools": {
                "profile": "minimal",
                "alsoAllow": list(OCP6R_CORTEX_TOOLS),
                "deny": DIRECT_TOOL_DENY + ["memory_search", "memory_get"],
            },
        }
    )
    active_config: dict[str, Any] = {
        "enabled": True,
        "agents": [agent_id],
        "allowedChatTypes": ["direct"],
        "queryMode": "message",
        "promptStyle": "precision-heavy",
        "toolsAllow": list(OCP6R_CORTEX_TOOLS),
        "promptAppend": OCP6R_CORTEX_PROMPT_APPEND,
        "logging": True,
        "persistTranscripts": True,
        "timeoutMs": 30000,
        "maxSummaryChars": 900,
        "recentUserTurns": 1,
        "recentAssistantTurns": 1,
    }
    if transcript_dir:
        active_config["transcriptDir"] = transcript_dir
    return {
        "agents": {"list": agents},
        "plugins": {
            "entries": {
                "active-memory": {
                    "enabled": True,
                    "config": active_config,
                },
                "nollm-memory-companion": {
                    "enabled": True,
                    "config": {
                        "pythonCommand": str(Path(sys.executable).resolve()),
                        "nollmRepoRoot": str(repo_root),
                        "workspaceRoot": str(workspace_root),
                        "sidecarOutDir": str(workspace_root / ".nollm-cortex"),
                        "commandTimeoutMs": 15000,
                        "maxSearchResults": 6,
                    },
                },
            }
        },
    }


def _existing_agents(config_before: Mapping[str, Any]) -> list[dict[str, Any]]:
    agents = ((config_before.get("agents") or {}) if isinstance(config_before.get("agents"), Mapping) else {}).get("list")
    if not isinstance(agents, Sequence) or isinstance(agents, (str, bytes)):
        return [{"id": "main"}]
    return [dict(agent) for agent in agents if isinstance(agent, Mapping)]


__all__ = [
    "DIRECT_TOOL_DENY",
    "OCP4_ACTIVE_MEMORY_PROMPT_APPEND",
    "OCP4_ACTIVE_MEMORY_TOOLS",
    "OCP4_AGENT_ID",
    "OCP6R_AGENT_ID",
    "OCP6R_CORTEX_PROMPT_APPEND",
    "OCP6R_CORTEX_TOOLS",
    "build_ocp4_active_memory_patch",
    "build_ocp6r_cortex_active_memory_patch",
]
