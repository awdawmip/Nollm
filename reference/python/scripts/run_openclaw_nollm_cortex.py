from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.openclaw_active_memory_config import (  # noqa: E402
    OCP9_CORTEX_AGENT_ID,
    OCP9_CORTEX_PROMPT_APPEND,
    OCP9_CORTEX_TOOLS,
    OCP9_LEGACY_NOLLM_TOOLS,
    OCP9_PRIMARY_AGENT_ID,
    OCP9_PROHIBITED_TOOLS,
    build_ocp9_live_cortex_reply_loop_patch,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Configure OpenClaw Active Memory as a bounded Nollm Cortex reply loop.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    configure = subparsers.add_parser("configure")
    configure.add_argument("--openclaw-bin", default="openclaw")
    configure.add_argument("--workspace", required=True, help="Read-only OpenClaw source workspace for Dream Packet/field production.")
    configure.add_argument("--config-path", default=None)
    configure.add_argument("--primary-agent", default=OCP9_PRIMARY_AGENT_ID)
    configure.add_argument("--cortex-agent", default=OCP9_CORTEX_AGENT_ID)
    configure.add_argument("--blind-workspace", default=None, help="Workspace for the user-facing blind primary agent.")
    configure.add_argument("--sidecar-out", default=None, help="Immutable Nollm field store. Defaults under workspace/.nollm-cortex.")
    configure.add_argument("--transcript-dir", default=None)
    configure.add_argument("--model", default=None)
    configure.add_argument("--apply", action="store_true")
    configure.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "configure":
        report = configure_cortex(args)
    else:
        raise AssertionError("unreachable command")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report.get("ok") is True else 1


def configure_cortex(args: argparse.Namespace) -> dict[str, object]:
    dry_run = bool(args.dry_run or not args.apply)
    openclaw = str(args.openclaw_bin)
    workspace = Path(args.workspace).resolve()
    repo_root = Path(__file__).resolve().parents[3]
    config_path = Path(args.config_path).expanduser().resolve() if args.config_path else _default_config_path(openclaw)
    blind_workspace = Path(args.blind_workspace).resolve() if args.blind_workspace else workspace.parent / f"{workspace.name}_blind_primary"
    sidecar_out = Path(args.sidecar_out).resolve() if args.sidecar_out else workspace / ".nollm-cortex"
    transcript_dir = str(Path(args.transcript_dir).resolve()) if args.transcript_dir else str(sidecar_out / "active_memory_transcripts")

    schema_report = _inspect_schema(openclaw)
    active_memory = _inspect_plugin(openclaw, "active-memory")
    companion = _inspect_plugin(openclaw, "nollm-memory-companion")
    config_before = json.loads(config_path.read_text(encoding="utf-8"))
    agents_before = _try_json(openclaw, ["agents", "list", "--json"], default=[])
    model = args.model or _derive_model(agents_before, config_before)

    patch = build_ocp9_live_cortex_reply_loop_patch(
        config_before=config_before,
        repo_root=repo_root,
        source_workspace_root=workspace,
        blind_workspace_root=blind_workspace,
        sidecar_out_dir=sidecar_out,
        primary_agent_id=args.primary_agent,
        cortex_agent_id=args.cortex_agent,
        model=model,
        transcript_dir=transcript_dir,
    )
    safety = _patch_safety(patch, primary_agent_id=args.primary_agent, cortex_agent_id=args.cortex_agent)
    if not all(safety.values()):
        return {
            "ok": False,
            "status": "unsafe_patch_rejected",
            "safety": safety,
        }

    patch_result = _apply_patch(openclaw, patch, dry_run=dry_run)
    validate = "dry_run_not_applied"
    agents_after = agents_before
    if not dry_run:
        validate = _run_text(openclaw, ["config", "validate"], timeout=60).strip()[:1000]
        agents_after = _try_json(openclaw, ["agents", "list", "--json"], default=[])
    visible_agents = _agent_ids(agents_after) if isinstance(agents_after, Sequence) else []

    return {
        "ok": dry_run or (args.primary_agent in visible_agents and args.cortex_agent in visible_agents),
        "status": "dry_run" if dry_run else "configured",
        "config_path": str(config_path),
        "schema_observed": schema_report["observed"],
        "active_memory_observed": active_memory["observed"],
        "active_memory_version": active_memory.get("version"),
        "nollm_companion_observed": companion["observed"],
        "nollm_companion_tools": companion.get("tools", []),
        "primary_agent": args.primary_agent,
        "cortex_agent": args.cortex_agent,
        "active_memory_trigger_agent": args.primary_agent,
        "model": model,
        "source_workspace": str(workspace),
        "blind_workspace": str(blind_workspace),
        "sidecar_out": str(sidecar_out),
        "transcript_dir": transcript_dir,
        "allowed_cortex_tools": list(OCP9_CORTEX_TOOLS),
        "prohibited_tools": list(OCP9_PROHIBITED_TOOLS),
        "cortex_prompt_requires_digest_owner": "You, the Cortex" in OCP9_CORTEX_PROMPT_APPEND,
        "safety": safety,
        "patch_result": _redact(patch_result),
        "validate": validate,
        "agents_visible": visible_agents,
    }


def _patch_safety(patch: Mapping[str, Any], *, primary_agent_id: str, cortex_agent_id: str) -> dict[str, bool]:
    agents = [item for item in ((patch.get("agents") or {}).get("list") or []) if isinstance(item, Mapping)]
    primary = next((item for item in agents if item.get("id") == primary_agent_id), {})
    cortex = next((item for item in agents if item.get("id") == cortex_agent_id), {})
    active = (((patch.get("plugins") or {}).get("entries") or {}).get("active-memory") or {}).get("config") or {}
    companion = (((patch.get("plugins") or {}).get("entries") or {}).get("nollm-memory-companion") or {}).get("config") or {}
    global_tools = patch.get("tools") or {}
    active_tools = list(active.get("toolsAllow") or [])
    primary_tools = primary.get("tools") or {}
    cortex_tools = cortex.get("tools") or {}
    primary_deny = set(primary_tools.get("deny") or [])
    cortex_deny = set(cortex_tools.get("deny") or [])
    global_also_allow = set(global_tools.get("alsoAllow") or [])
    prohibited = set(OCP9_PROHIBITED_TOOLS)
    legacy = set(OCP9_LEGACY_NOLLM_TOOLS)
    return {
        "primary_context_injection_never": primary.get("contextInjection") == "never",
        "primary_bootstrap_bounded": primary.get("bootstrapMaxChars") == 1 and primary.get("bootstrapTotalMaxChars") == 1,
        "primary_memory_search_disabled": primary.get("memorySearch") == {"provider": "none", "fallback": "none"},
        "primary_allows_only_ocp9_for_active_memory": primary_tools.get("alsoAllow") == OCP9_CORTEX_TOOLS,
        "primary_denies_prohibited_tools": prohibited.issubset(primary_deny),
        "cortex_allows_only_ocp9_tools": cortex_tools.get("alsoAllow") == OCP9_CORTEX_TOOLS,
        "cortex_denies_prohibited_tools": prohibited.issubset(cortex_deny),
        "global_tools_allow_ocp9_surface": set(OCP9_CORTEX_TOOLS).issubset(global_also_allow),
        "global_tools_exclude_legacy_nollm": not (global_also_allow & legacy),
        "active_memory_targets_primary": active.get("agents") == [primary_agent_id],
        "active_memory_tools_exact": active_tools == OCP9_CORTEX_TOOLS,
        "active_memory_excludes_legacy_and_search": not (set(active_tools) & (legacy | {"memory_search", "memory_get", "read"})),
        "prompt_requires_entry_choice": "explicitly choose the entry" in str(active.get("promptAppend")),
        "prompt_requires_digest_owner": "You, the Cortex" in str(active.get("promptAppend")),
        "prompt_surfaces_stale": "field_stale" in str(active.get("promptAppend")),
        "companion_has_source_workspace": bool(companion.get("workspaceRoot")),
        "companion_has_sidecar_out": bool(companion.get("sidecarOutDir")),
    }


def _inspect_schema(openclaw: str) -> dict[str, object]:
    try:
        schema = _run_text(openclaw, ["config", "schema"], timeout=30)
    except Exception as exc:
        return {"observed": False, "error": str(exc)[:500]}
    return {"observed": bool(schema.strip()), "bytes": len(schema.encode("utf-8"))}


def _inspect_plugin(openclaw: str, plugin_id: str) -> dict[str, object]:
    try:
        data = json.loads(_run_text(openclaw, ["plugins", "inspect", plugin_id, "--json"], timeout=60))
    except Exception as exc:
        return {"observed": False, "plugin_id": plugin_id, "error": str(exc)[:500]}
    plugin = data.get("plugin") if isinstance(data, Mapping) else {}
    contracts = plugin.get("contracts") if isinstance(plugin, Mapping) else {}
    tools = []
    if isinstance(contracts, Mapping) and isinstance(contracts.get("tools"), list):
        tools = [str(item) for item in contracts["tools"]]
    if not tools and isinstance(plugin, Mapping) and isinstance(plugin.get("toolNames"), list):
        tools = [str(item) for item in plugin["toolNames"]]
    return {
        "observed": True,
        "plugin_id": plugin_id,
        "status": plugin.get("status") if isinstance(plugin, Mapping) else None,
        "version": plugin.get("version") if isinstance(plugin, Mapping) else None,
        "tools": tools,
    }


def _default_config_path(openclaw: str) -> Path:
    raw = _run_text(openclaw, ["config", "file"], timeout=60).strip()
    if raw.startswith("~"):
        raw = str(Path.home()) + raw[1:]
    return Path(raw).resolve()


def _derive_model(agents: object, config: Mapping[str, Any]) -> str:
    if isinstance(agents, list):
        for item in agents:
            if isinstance(item, Mapping) and item.get("isDefault") is True and isinstance(item.get("model"), str):
                return str(item["model"])
        for item in agents:
            if isinstance(item, Mapping) and isinstance(item.get("model"), str):
                return str(item["model"])
    defaults = ((config.get("agents") or {}) if isinstance(config.get("agents"), Mapping) else {}).get("defaults")
    if isinstance(defaults, Mapping):
        model = defaults.get("model")
        if isinstance(model, Mapping) and isinstance(model.get("primary"), str):
            return str(model["primary"])
        if isinstance(model, str):
            return model
    return "ollama/qwen2.5:7b"


def _apply_patch(openclaw: str, patch: Mapping[str, object], *, dry_run: bool) -> object:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        json.dump(patch, handle, ensure_ascii=False, indent=2)
        patch_path = Path(handle.name)
    try:
        args = ["config", "patch", "--file", str(patch_path)]
        if dry_run:
            args.extend(["--dry-run", "--json"])
        output = _run_text(openclaw, args, timeout=60)
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {"stdout": output.strip()[:1000]}
    finally:
        patch_path.unlink(missing_ok=True)


def _try_json(openclaw: str, args: list[str], *, default: object) -> object:
    try:
        return json.loads(_run_text(openclaw, args, timeout=60))
    except Exception:
        return default


def _run_text(openclaw: str, args: list[str], *, timeout: int) -> str:
    completed = subprocess.run(
        _command_prefix(openclaw) + args,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or f"OpenClaw command failed: {args}").strip())
    return completed.stdout


def _command_prefix(executable: str) -> list[str]:
    path = Path(executable)
    if sys.platform.startswith("win") and executable.lower().endswith((".cmd", ".ps1")):
        base = path.resolve().parent
        node = base / "node.exe"
        mjs = base / "node_modules" / "openclaw" / "openclaw.mjs"
        if node.exists() and mjs.exists():
            return [str(node), str(mjs)]
        return ["cmd.exe", "/d", "/c", executable]
    return [executable]


def _agent_ids(agents: object) -> list[str]:
    if not isinstance(agents, Sequence) or isinstance(agents, (str, bytes)):
        return []
    return [str(item.get("id")) for item in agents if isinstance(item, Mapping) and item.get("id")]


def _redact(value: object) -> object:
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            if any(secret in str(key).lower() for secret in ("token", "secret", "key", "password")):
                result[key] = "<redacted>"
            else:
                result[key] = _redact(item)
        return result
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
