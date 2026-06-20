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
    "nollm_field_overview",
    "nollm_open_well",
    "nollm_surface",
    "nollm_focus",
    "nollm_drift",
    "nollm_read",
    "nollm_recall_trace",
]
OCP6R_CORTEX_PROMPT_APPEND = (
    "Act as Nollm Cortex, not as a raw memory searcher. "
    "Use nollm_field_overview -> choose entry shard -> nollm_open_well with your explicit non-negative anchor_vector; keep the returned well_id -> "
    "nollm_surface -> choose focus -> nollm_focus -> optional nollm_drift -> explicit return toward the entry task -> "
    "nollm_read with that well_id for exact shard reads -> nollm_recall_trace for logging. "
    "A well is bound to one immutable field revision; do not read outside it. "
    "You, the Cortex, write the compact Recall Digest or NONE; Core does not compose prose. "
    "No tool output alone is source truth. Drift labels are orientation only. "
    "Do not use memory_search or memory_get as the Nollm internal model."
)
OCP7_DREAMER_AGENT_ID = "nollm-dreamer"
OCP7_DREAMER_PROMPT_APPEND = (
    "Act only as the Nollm Dreamer. Emit exactly one JSON object using schema nollm.dreamer_delta.v1. "
    "Use only the supplied read-only source snapshot metadata and bounded diff. "
    "Do not answer a user, rank candidates, search memory, write files, or emit q/r/layer/HexAddress coordinates. "
    "Core owns final honeycomb placement."
)
OCP9_PRIMARY_AGENT_ID = "ocp9-nollm-primary-blind"
OCP9_CORTEX_AGENT_ID = "ocp9-nollm-cortex"
OCP9_CORTEX_TOOLS = OCP6R_CORTEX_TOOLS + ["nollm_memory_status"]
OCP9_LEGACY_NOLLM_TOOLS = [
    "nollm_memory_recall",
    "nollm_memory_search",
    "nollm_memory_get",
    "nollm_memory_write_candidate",
    "nollm_memory_commit_candidate",
]
OCP9_PROHIBITED_TOOLS = DIRECT_TOOL_DENY + [
    "memory_search",
    "memory_get",
] + OCP9_LEGACY_NOLLM_TOOLS
OCP9_CORTEX_PROMPT_APPEND = (
    "Act as the Nollm Cortex for Active Memory before the primary reply. "
    "Use nollm_memory_status or nollm_field_overview first to detect field availability and field_stale; status is only a stale gate, never recall evidence. "
    "If field_stale is true, write NONE or a compact 'field stale - refresh required' Recall Digest; do not present stale facts as current. "
    "Required path: nollm_field_overview -> you explicitly choose the entry shard -> nollm_open_well with your explicit non-negative anchor_vector -> "
    "nollm_surface -> you choose the focus target -> nollm_focus -> optional nollm_drift for lateral/return orientation -> "
    "nollm_read with the current well_id for exact dream-shard reads -> nollm_recall_trace. "
    "For bridge/project questions or messages naming multiple entities, inspect both target_scale bridge and target_scale fine with nollm_surface before deciding a shard is missing. "
    "For every named entity visible in bridge/fine surface, focus and read the exact shard, then include every read shard in nollm_recall_trace. "
    "When the user asks for an update, status, blockers, roadmap, relationship, or preference, include only facts read from shards; if a requested fact is not read, state that no current recall for that fact was found. "
    "After nollm_recall_trace, immediately write one compact Recall Digest under 600 characters or NONE; do not keep exploring. "
    "You, the Cortex, write the compact Recall Digest or NONE for injection into the primary reply. "
    "Core only executes deterministic geometry and never composes prose, selects the semantic entry, ranks by query text, or reads raw source chunks. "
    "Do not call read, exec, process, edit, write, memory_search, memory_get, or legacy nollm_memory_recall/search/get tools. "
    "No tool output alone is source truth; drift_class is orientation only and never maps to trust, status, permission, or rejection."
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
    tools_patch = _build_ocp9_global_tools_patch(config_before)
    return {
        "agents": {"list": agents},
        "tools": tools_patch,
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


def build_ocp7_dreamer_agent_patch(
    *,
    config_before: Mapping[str, Any],
    workspace_root: Path,
    agent_id: str = OCP7_DREAMER_AGENT_ID,
    model: str = "kimi/kimi-for-coding",
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
                "alsoAllow": [],
                "deny": DIRECT_TOOL_DENY + ["memory_search", "memory_get", "nollm_memory_search", "nollm_memory_get"],
            },
        }
    )
    return {"agents": {"list": agents}}


def build_ocp9_live_cortex_reply_loop_patch(
    *,
    config_before: Mapping[str, Any],
    repo_root: Path,
    source_workspace_root: Path,
    blind_workspace_root: Path,
    sidecar_out_dir: Path,
    primary_agent_id: str = OCP9_PRIMARY_AGENT_ID,
    cortex_agent_id: str = OCP9_CORTEX_AGENT_ID,
    model: str = "kimi/kimi-for-coding",
    transcript_dir: str | None = None,
) -> dict[str, Any]:
    agents = _existing_agents(config_before)
    agents = [agent for agent in agents if agent.get("id") not in {primary_agent_id, cortex_agent_id}]
    agents.append(_build_ocp9_primary_agent(primary_agent_id, blind_workspace_root, model))
    agents.append(_build_ocp9_cortex_agent(cortex_agent_id, blind_workspace_root, model))
    active_config: dict[str, Any] = {
        "enabled": True,
        "agents": [primary_agent_id],
        "model": model,
        "allowedChatTypes": ["direct"],
        "queryMode": "message",
        "promptStyle": "precision-heavy",
        "toolsAllow": list(OCP9_CORTEX_TOOLS),
        "promptAppend": OCP9_CORTEX_PROMPT_APPEND,
        "logging": True,
        "persistTranscripts": True,
        "timeoutMs": 120000,
        "maxSummaryChars": 900,
        "recentUserTurns": 1,
        "recentAssistantTurns": 0,
    }
    if transcript_dir:
        active_config["transcriptDir"] = transcript_dir
    tools_patch = _build_ocp9_global_tools_patch(config_before)
    return {
        "agents": {"list": agents},
        "tools": tools_patch,
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
                        "workspaceRoot": str(source_workspace_root),
                        "sidecarOutDir": str(sidecar_out_dir),
                        "commandTimeoutMs": 30000,
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


def _build_ocp9_primary_agent(agent_id: str, workspace_root: Path, model: str) -> dict[str, Any]:
    return {
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
            "alsoAllow": list(OCP9_CORTEX_TOOLS),
            "deny": OCP9_PROHIBITED_TOOLS,
        },
    }


def _build_ocp9_cortex_agent(agent_id: str, workspace_root: Path, model: str) -> dict[str, Any]:
    return {
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
            "alsoAllow": list(OCP9_CORTEX_TOOLS),
            "deny": OCP9_PROHIBITED_TOOLS,
        },
    }


def _build_ocp9_global_tools_patch(config_before: Mapping[str, Any]) -> dict[str, Any]:
    existing = config_before.get("tools") if isinstance(config_before.get("tools"), Mapping) else {}
    patch: dict[str, Any] = {}
    if isinstance(existing, Mapping) and isinstance(existing.get("profile"), str):
        patch["profile"] = existing["profile"]
    also_allow = _merge_tool_list(existing.get("alsoAllow") if isinstance(existing, Mapping) else None, OCP9_CORTEX_TOOLS)
    patch["alsoAllow"] = also_allow
    allow = existing.get("allow") if isinstance(existing, Mapping) else None
    if isinstance(allow, Sequence) and not isinstance(allow, (str, bytes)):
        patch["allow"] = _merge_tool_list(allow, OCP9_CORTEX_TOOLS)
    deny = existing.get("deny") if isinstance(existing, Mapping) else None
    if isinstance(deny, Sequence) and not isinstance(deny, (str, bytes)):
        patch["deny"] = [str(item) for item in deny if str(item) not in set(OCP9_CORTEX_TOOLS)]
    return patch


def _merge_tool_list(existing: object, additions: Sequence[str]) -> list[str]:
    forbidden = set(OCP9_LEGACY_NOLLM_TOOLS)
    values: list[str] = []
    if isinstance(existing, Sequence) and not isinstance(existing, (str, bytes)):
        values.extend(str(item) for item in existing if str(item) not in forbidden)
    for item in additions:
        if item not in values:
            values.append(item)
    return values


__all__ = [
    "DIRECT_TOOL_DENY",
    "OCP4_ACTIVE_MEMORY_PROMPT_APPEND",
    "OCP4_ACTIVE_MEMORY_TOOLS",
    "OCP4_AGENT_ID",
    "OCP6R_AGENT_ID",
    "OCP6R_CORTEX_PROMPT_APPEND",
    "OCP6R_CORTEX_TOOLS",
    "OCP7_DREAMER_AGENT_ID",
    "OCP7_DREAMER_PROMPT_APPEND",
    "OCP9_CORTEX_AGENT_ID",
    "OCP9_CORTEX_PROMPT_APPEND",
    "OCP9_CORTEX_TOOLS",
    "OCP9_LEGACY_NOLLM_TOOLS",
    "OCP9_PRIMARY_AGENT_ID",
    "OCP9_PROHIBITED_TOOLS",
    "build_ocp4_active_memory_patch",
    "build_ocp6r_cortex_active_memory_patch",
    "build_ocp7_dreamer_agent_patch",
    "build_ocp9_live_cortex_reply_loop_patch",
]
