from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))


STALE_NOLLM_TOOLS = {
    "nollm_memory_status",
    "nollm_field_overview",
    "nollm_open_well",
    "nollm_surface",
    "nollm_focus",
    "nollm_drift",
    "nollm_read",
    "nollm_recall_trace",
    "nollm_memory_remember",
    "nollm_memory_recall",
    "nollm_memory_get",
}
MUTATION_TOOLS = {"write", "edit", "apply_patch", "exec", "process"}
LEGACY_MEMORY_TOOLS = {
    "memory_search",
    "memory_get",
    "memory_store",
    "memory_write",
    "nollm_memory_search",
    "nollm_memory_write_candidate",
    "nollm_memory_commit_candidate",
}
LEGACY_SOURCE_NAMES = {"MEMORY.md", "DREAMS.md"}
DEFAULT_TRIAL_AGENT_ID = "w2-02-nollm-active-trial"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 120) -> dict[str, Any]:
    resolved = list(cmd)
    executable = shutil.which(resolved[0])
    if executable:
        resolved[0] = executable
    proc = subprocess.run(
        resolved,
        cwd=str(cwd) if cwd else None,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        shell=False,
    )
    return {
        "cmd": cmd,
        "resolved_cmd": resolved,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout.splitlines()[-20:],
        "stderr_tail": proc.stderr.splitlines()[-20:],
    }


def _backup_path(out: Path) -> Path:
    return out / "private" / "openclaw-config.backup.json"


def _legacy_hashes(workspace: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    candidates = [workspace / name for name in sorted(LEGACY_SOURCE_NAMES)]
    memory_dir = workspace / "memory"
    if memory_dir.exists():
        candidates.extend(sorted(memory_dir.rglob("*.md")))
    for path in candidates:
        if path.exists() and path.is_file():
            stat = path.stat()
            result[path.relative_to(workspace).as_posix()] = {
                "sha256": _sha256_file(path),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
    return result


def _collect_tool_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"allow", "alsoAllow", "deny", "tools", "tool_names", "toolNames"} and isinstance(item, list):
                names.update(str(v) for v in item if isinstance(v, str))
            names.update(_collect_tool_names(item))
    elif isinstance(value, list):
        for item in value:
            names.update(_collect_tool_names(item))
    return names


def _remove_stale_tools(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in list(value.items()):
            if key in {"allow", "alsoAllow", "deny", "tools", "tool_names", "toolNames"} and isinstance(item, list):
                value[key] = [tool for tool in item if tool not in STALE_NOLLM_TOOLS]
            else:
                _remove_stale_tools(item)
    elif isinstance(value, list):
        for item in value:
            _remove_stale_tools(item)


def _trial_agent(config: dict[str, Any], agent_id: str) -> dict[str, Any] | None:
    agents = config.get("agents") if isinstance(config.get("agents"), dict) else {}
    for agent in agents.get("list") or []:
        if isinstance(agent, dict) and agent.get("id") == agent_id:
            return agent
    return None


def _disabled_entry_config_issues(config: dict[str, Any]) -> list[str]:
    entries = ((config.get("plugins") or {}).get("entries") or {})
    issues: list[str] = []
    for name in ("nollm-memory-companion", "active-memory", "memory-core"):
        entry = entries.get(name)
        if isinstance(entry, dict) and entry.get("enabled") is False and "config" in entry:
            issues.append(f"{name}: disabled entry still has config")
    return issues


def _runtime_assertions(config: dict[str, Any]) -> dict[str, Any]:
    plugins = config.get("plugins") if isinstance(config.get("plugins"), dict) else {}
    slots = plugins.get("slots") if isinstance(plugins.get("slots"), dict) else {}
    entries = plugins.get("entries") if isinstance(plugins.get("entries"), dict) else {}
    tool_names = _collect_tool_names(config.get("tools", {}))
    stale_tools = sorted(tool_names & STALE_NOLLM_TOOLS)
    global_mutation_tools = sorted(tool_names & MUTATION_TOOLS)
    trial_agent = _trial_agent(config, DEFAULT_TRIAL_AGENT_ID)
    trial_tools = trial_agent.get("tools") if isinstance(trial_agent, dict) and isinstance(trial_agent.get("tools"), dict) else {}
    trial_deny = set(tool for tool in trial_tools.get("deny", []) if isinstance(tool, str))
    trial_exposed = sorted((set(trial_tools.get("alsoAllow", [])) | set(trial_tools.get("allow", []))) & (MUTATION_TOOLS | LEGACY_MEMORY_TOOLS | STALE_NOLLM_TOOLS))
    trial_missing_denies = sorted((MUTATION_TOOLS | LEGACY_MEMORY_TOOLS | STALE_NOLLM_TOOLS) - trial_deny)
    nollm_entry = entries.get("nollm") if isinstance(entries.get("nollm"), dict) else {}
    disabled_issues = _disabled_entry_config_issues(config)
    ok = (
        slots.get("memory") == "nollm"
        and nollm_entry.get("enabled") is True
        and not stale_tools
        and not global_mutation_tools
        and not disabled_issues
        and isinstance(trial_agent, dict)
        and not trial_exposed
        and not trial_missing_denies
        and trial_agent.get("contextInjection") == "never"
        and (trial_agent.get("memorySearch") or {}).get("provider") == "none"
    )
    return {
        "ok": ok,
        "memory_slot": slots.get("memory"),
        "nollm_enabled": nollm_entry.get("enabled"),
        "stale_nollm_tools": stale_tools,
        "mutation_tools": global_mutation_tools,
        "disabled_entry_config_issues": disabled_issues,
        "primary_nollm_tools_exposed": False if not stale_tools else True,
        "trial_agent_id": DEFAULT_TRIAL_AGENT_ID,
        "trial_agent_present": isinstance(trial_agent, dict),
        "trial_agent_context_injection": trial_agent.get("contextInjection") if isinstance(trial_agent, dict) else None,
        "trial_agent_memory_provider": (trial_agent.get("memorySearch") or {}).get("provider") if isinstance(trial_agent, dict) else None,
        "trial_agent_exposed_forbidden_tools": trial_exposed,
        "trial_agent_missing_denies": trial_missing_denies,
    }


def _ensure_private_backup(config_path: Path, out: Path) -> Path:
    backup = _backup_path(out)
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(config_path, backup)
    return backup


def _configure_active_trial(config: dict[str, Any], args: argparse.Namespace) -> None:
    plugins = config.setdefault("plugins", {})
    if not isinstance(plugins, dict):
        raise ValueError("plugins must be an object")
    entries = plugins.setdefault("entries", {})
    if not isinstance(entries, dict):
        raise ValueError("plugins.entries must be an object")
    slots = plugins.setdefault("slots", {})
    if not isinstance(slots, dict):
        raise ValueError("plugins.slots must be an object")

    slots["memory"] = "nollm"
    entries.setdefault("nollm", {})["enabled"] = True
    nollm_config = entries["nollm"].setdefault("config", {})
    if args.repo_root:
        nollm_config["nollmRepoRoot"] = str(Path(args.repo_root).resolve()).replace(os.sep, "/")
    if args.python_executable:
        nollm_config["pythonExecutable"] = str(Path(args.python_executable).resolve()).replace(os.sep, "/")
    nollm_config.setdefault("trialMode", "active_empirical_v1")
    nollm_config.setdefault("captureMode", "deterministic_explicit_v1")

    for name in ("nollm-memory-companion", "active-memory", "memory-core"):
        entry = entries.setdefault(name, {})
        if isinstance(entry, dict):
            entry["enabled"] = False
            entry.pop("config", None)

    _remove_stale_tools(config)

    agents = config.setdefault("agents", {})
    if not isinstance(agents, dict):
        raise ValueError("agents must be an object")
    agent_list = agents.setdefault("list", [])
    if not isinstance(agent_list, list):
        raise ValueError("agents.list must be an array")
    agent = _trial_agent(config, DEFAULT_TRIAL_AGENT_ID)
    if agent is None:
        agent = {"id": DEFAULT_TRIAL_AGENT_ID}
        agent_list.append(agent)
    workspace = str(Path(args.workspace).resolve())
    agent.update(
        {
            "name": DEFAULT_TRIAL_AGENT_ID,
            "workspace": workspace,
            "bootstrapMaxChars": 1,
            "bootstrapTotalMaxChars": 1,
            "contextInjection": "never",
            "memorySearch": {"provider": "none", "fallback": "none"},
            "tools": {
                "profile": "minimal",
                "alsoAllow": [],
                "deny": sorted(MUTATION_TOOLS | LEGACY_MEMORY_TOOLS | STALE_NOLLM_TOOLS),
            },
        }
    )


def _snapshot(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    workspace = Path(args.workspace).resolve()
    out = Path(args.out).resolve()
    config = _read_json(config_path)
    backup = _ensure_private_backup(config_path, out)
    report = {
        "schema": "nollm.w2_02.active_trial_snapshot.v1",
        "ok": True,
        "created_at": _now(),
        "config_sha256": _sha256_file(config_path),
        "plugins_slots_memory": ((config.get("plugins") or {}).get("slots") or {}).get("memory"),
        "runtime_assertions": _runtime_assertions(config),
        "legacy_sources": _legacy_hashes(workspace),
        "private_backup": str(backup),
    }
    _write_json(out / "snapshot.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _assert_runtime(args: argparse.Namespace) -> int:
    config = _read_json(Path(args.config).resolve())
    assertions = _runtime_assertions(config)
    report = {
        "schema": "nollm.w2_02.active_trial_runtime_assertions.v1",
        "ok": assertions["ok"],
        "created_at": _now(),
        "assertions": assertions,
    }
    if args.out:
        _write_json(Path(args.out).resolve() / "runtime-assertions.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def _hash_legacy(args: argparse.Namespace) -> int:
    report = {
        "schema": "nollm.w2_02.legacy_hashes.v1",
        "ok": True,
        "created_at": _now(),
        "legacy_sources": _legacy_hashes(Path(args.workspace).resolve()),
    }
    if args.out:
        _write_json(Path(args.out).resolve() / f"legacy-hashes-{args.stage}.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _apply(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    workspace = Path(args.workspace).resolve()
    out = Path(args.out).resolve()
    before_hashes = _legacy_hashes(workspace)
    backup = _ensure_private_backup(config_path, out)
    config = _read_json(config_path)
    _configure_active_trial(config, args)
    _write_json(config_path, config)
    steps: list[dict[str, Any]] = []
    provider_dir = Path(args.repo_root).resolve() / "integrations" / "openclaw" / "nollm-memory-provider"
    if provider_dir.exists():
        steps.append(_run(["npm", "run", "build"], cwd=provider_dir, timeout=180))
    steps.append(_run(["openclaw", "config", "validate"], timeout=60))
    if all(step["returncode"] == 0 for step in steps):
        steps.append(_run(["openclaw", "gateway", "restart"], timeout=120))
    after_hashes = _legacy_hashes(workspace)
    assertions = _runtime_assertions(_read_json(config_path))
    ok = all(step["returncode"] == 0 for step in steps) and assertions["ok"] and before_hashes == after_hashes
    report = {
        "schema": "nollm.w2_02.active_trial_operator_step.v1",
        "ok": ok,
        "command": "apply",
        "created_at": _now(),
        "backup": str(backup),
        "legacy_sources_unchanged": before_hashes == after_hashes,
        "runtime_assertions": assertions,
        "steps": steps,
    }
    _write_json(out / "apply.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


def _rollback(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    workspace = Path(args.workspace).resolve()
    out = Path(args.out).resolve()
    backup = _backup_path(out)
    before_hashes = _legacy_hashes(workspace)
    if not backup.exists():
        report = {
            "schema": "nollm.w2_02.active_trial_operator_step.v1",
            "ok": False,
            "command": "rollback",
            "created_at": _now(),
            "error": {"code": "backup_missing", "message": str(backup)},
        }
        _write_json(out / "rollback.json", report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1
    shutil.copy2(backup, config_path)
    steps = [_run(["openclaw", "config", "validate"], timeout=60)]
    if steps[0]["returncode"] == 0:
        steps.append(_run(["openclaw", "gateway", "restart"], timeout=120))
    after_hashes = _legacy_hashes(workspace)
    ok = all(step["returncode"] == 0 for step in steps) and before_hashes == after_hashes
    report = {
        "schema": "nollm.w2_02.active_trial_operator_step.v1",
        "ok": ok,
        "command": "rollback",
        "created_at": _now(),
        "legacy_sources_unchanged": before_hashes == after_hashes,
        "steps": steps,
    }
    _write_json(out / "rollback.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


def _report(args: argparse.Namespace) -> int:
    out = Path(args.out).resolve()
    files = {}
    for path in sorted(out.glob("*.json")):
        files[path.name] = _sha256_file(path)
    report = {
        "schema": "nollm.w2_02.active_trial_report_manifest.v1",
        "ok": True,
        "created_at": _now(),
        "artifact_hashes": files,
    }
    _write_json(out / "report-manifest.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _blocked_command(name: str, args: argparse.Namespace) -> int:
    report = {
        "schema": "nollm.w2_02.active_trial_operator_step.v1",
        "ok": False,
        "command": name,
        "status": "blocked_requires_openclaw_cli",
        "message": "This controller records the required step but will not fake a live OpenClaw install/reload without a configured CLI command.",
        "created_at": _now(),
    }
    if args.out:
        _write_json(Path(args.out).resolve() / f"{name}.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="W2-02 Nollm active-memory trial controller.")
    parser.add_argument("command", choices=["snapshot", "apply", "assert-runtime", "trial", "rollback", "reapply", "report", "hash-legacy"])
    parser.add_argument("--config", help="OpenClaw JSON config path")
    parser.add_argument("--workspace", default=".", help="Workspace containing MEMORY.md/DREAMS.md/memory/*.md")
    parser.add_argument("--out", default=".local-runs/w2-02-active-trial", help="Private local output directory")
    parser.add_argument("--stage", default="manual", help="Stage label for hash-legacy")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[3]), help="Nollm repository root")
    parser.add_argument("--python-executable", default=sys.executable, help="Configured absolute Python executable")
    args = parser.parse_args(argv)

    if args.command in {"snapshot", "apply", "assert-runtime", "rollback", "reapply"} and not args.config:
        parser.error(f"{args.command} requires --config")
    if args.command == "snapshot":
        return _snapshot(args)
    if args.command == "assert-runtime":
        return _assert_runtime(args)
    if args.command == "hash-legacy":
        return _hash_legacy(args)
    if args.command == "apply":
        return _apply(args)
    if args.command == "reapply":
        return _apply(args)
    if args.command == "rollback":
        return _rollback(args)
    if args.command == "report":
        return _report(args)
    return _blocked_command(args.command, args)


if __name__ == "__main__":
    raise SystemExit(main())
