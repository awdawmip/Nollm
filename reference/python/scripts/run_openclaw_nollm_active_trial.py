from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from nollm.w2_forensic import (
    create_operation,
    operation_root,
    quarantine_operation,
    set_operation_state,
    validate_operation_id,
    validate_trial_id,
    write_json as _write_w2_json,
)

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
MUTATION_TOOLS = {"write", "edit", "apply_patch", "exec", "process", "file_write"}
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
DEFAULT_TRIAL_ID_PREFIX = "w2-05"
ACTIVE_STATUS_SCHEMA = "nollm.active_memory_status.v1"
ACTIVE_PREPARE_SCHEMA = "nollm.active_memory_prepare.v1"
ACTIVE_TRIAL_REPORT_SCHEMA = "nollm.active_memory_trial_report.v1"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _detect_config_format(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        return {
            "format": "json5_or_unsupported",
            "patch_route": "blocked_before_mutation",
            "ok": False,
            "error": f"json_parse_failed:{exc.lineno}:{exc.colno}",
        }
    return {"format": "json", "patch_route": "staged_json_atomic_replace", "ok": True}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    _write_w2_json(path, data)


def _posix(path: Path | str) -> str:
    return str(Path(path).resolve()).replace(os.sep, "/")


def _redact_text(text: str) -> str:
    home = str(Path.home())
    text = text.replace(home, "<HOME>").replace(home.replace("\\", "/"), "<HOME>")
    text = re.sub(r"Bearer\s+\S+", "Bearer <REDACTED>", text, flags=re.I)
    text = re.sub(r"sk-[A-Za-z0-9_-]+", "sk-<REDACTED>", text)
    text = re.sub(r"github_pat_\S+|ghp_\S+", "<GITHUB_TOKEN_REDACTED>", text)
    text = re.sub(r"(?i)(password|cookie|api[_-]?key)\s*[:=]\s*\S+", r"\1=<REDACTED>", text)
    text = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<UUID>", text, flags=re.I)
    return text


def _redact_obj(value: Any) -> Any:
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, list):
        return [_redact_obj(v) for v in value]
    if isinstance(value, dict):
        blocked = {"token", "cookie", "password", "api_key", "apikey"}
        return {str(k): _redact_obj(v) for k, v in value.items() if str(k).lower() not in blocked}
    return value


@dataclass(frozen=True)
class TargetBinding:
    openclaw_bin: Path
    config: Path
    profile: str | None
    workspace: Path
    repo_root: Path
    python_executable: Path
    out: Path
    target_agent_id: str
    trial_id: str

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "TargetBinding":
        required = {
            "openclaw_bin": args.openclaw_bin,
            "config": args.config,
            "workspace": args.workspace,
            "repo_root": args.repo_root,
            "python_executable": args.python_executable,
            "out": args.out,
            "target_agent_id": args.target_agent_id,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"missing required target arguments: {', '.join(missing)}")
        raw_paths = {name: Path(value) for name, value in required.items() if name != "target_agent_id"}
        for name in ("openclaw_bin", "config", "workspace", "repo_root", "python_executable"):
            if not raw_paths[name].is_absolute():
                raise ValueError(f"{name} must be absolute")
        paths = {name: value.resolve() for name, value in raw_paths.items()}
        for name in ("openclaw_bin", "config", "workspace", "repo_root", "python_executable"):
            if not paths[name].exists():
                raise ValueError(f"{name} does not exist")
        trial_id = args.trial_id or f"{DEFAULT_TRIAL_ID_PREFIX}-{_stamp()}"
        validate_trial_id(trial_id)
        return cls(
            openclaw_bin=paths["openclaw_bin"],
            config=paths["config"],
            profile=args.profile,
            workspace=paths["workspace"],
            repo_root=paths["repo_root"],
            python_executable=paths["python_executable"],
            out=paths["out"],
            target_agent_id=args.target_agent_id,
            trial_id=trial_id,
        )

    def argv(self, *parts: str) -> list[str]:
        argv = [str(self.openclaw_bin)]
        if self.profile:
            argv.extend(["--profile", self.profile])
        argv.extend(parts)
        return argv

    def env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["OPENCLAW_CONFIG_PATH"] = str(self.config)
        return env

    def redacted(self) -> dict[str, Any]:
        return {
            "openclaw_bin": _redact_text(str(self.openclaw_bin)),
            "config": _redact_text(str(self.config)),
            "profile": self.profile,
            "workspace": _redact_text(str(self.workspace)),
            "repo_root": _redact_text(str(self.repo_root)),
            "python_executable": _redact_text(str(self.python_executable)),
            "target_agent_id": self.target_agent_id,
            "trial_id": self.trial_id,
            "binding_mode": "OPENCLAW_CONFIG_PATH+--profile" if self.profile else "OPENCLAW_CONFIG_PATH",
        }


def _run_bound(binding: TargetBinding, argv: list[str], *, cwd: Path | None = None, timeout: int = 120) -> dict[str, Any]:
    started_at = _now()
    resolved_argv = list(argv)
    if resolved_argv and not Path(resolved_argv[0]).is_absolute():
        resolved = shutil.which(resolved_argv[0])
        if resolved:
            resolved_argv[0] = resolved
    try:
        proc = subprocess.run(
            resolved_argv,
            cwd=str(cwd or binding.repo_root),
            env=binding.env(),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            shell=False,
        )
    except FileNotFoundError as exc:
        return {
            "schema": "nollm.w2_03.command_receipt.v1",
            "started_at": started_at,
            "argv_shape": [_redact_text(a) for a in argv],
            "binding": binding.redacted(),
            "exit_code": 127,
            "stdout_bytes": 0,
            "stderr_bytes": len(str(exc).encode("utf-8", errors="replace")),
            "stdout_tail": "",
            "stderr_tail": _redact_text(str(exc))[-4000:],
            "parsed_safe_result": None,
        }
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    parsed = None
    try:
        parsed = json.loads(stdout)
    except Exception:
        pass
    return {
        "schema": "nollm.w2_03.command_receipt.v1",
        "started_at": started_at,
        "argv_shape": [_redact_text(a) for a in argv],
        "binding": binding.redacted(),
        "exit_code": proc.returncode,
        "stdout_bytes": len(stdout.encode("utf-8", errors="replace")),
        "stderr_bytes": len(stderr.encode("utf-8", errors="replace")),
        "stdout_tail": _redact_text(stdout)[-4000:],
        "stderr_tail": _redact_text(stderr)[-4000:],
        "parsed_safe_result": _redact_obj(parsed) if isinstance(parsed, dict) else None,
    }


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


def _config_assertions(config: dict[str, Any], binding: TargetBinding) -> dict[str, Any]:
    plugins = config.get("plugins") if isinstance(config.get("plugins"), dict) else {}
    slots = plugins.get("slots") if isinstance(plugins.get("slots"), dict) else {}
    entries = plugins.get("entries") if isinstance(plugins.get("entries"), dict) else {}
    tool_names = _collect_tool_names(config.get("tools", {}))
    trial_agent = _trial_agent(config, binding.target_agent_id)
    trial_tools = trial_agent.get("tools") if isinstance(trial_agent, dict) and isinstance(trial_agent.get("tools"), dict) else {}
    trial_deny = set(tool for tool in trial_tools.get("deny", []) if isinstance(tool, str))
    forbidden = MUTATION_TOOLS | LEGACY_MEMORY_TOOLS | STALE_NOLLM_TOOLS
    trial_exposed = sorted((set(trial_tools.get("alsoAllow", [])) | set(trial_tools.get("allow", []))) & forbidden)
    nollm_entry = entries.get("nollm") if isinstance(entries.get("nollm"), dict) else {}
    cfg = nollm_entry.get("config") if isinstance(nollm_entry.get("config"), dict) else {}
    required = {
        "pythonExecutable", "pythonArgs", "nollmRepoRoot", "workspaceRoot", "nativeStoreRoot", "trialRoot",
        "commandTimeoutMs", "maxFacts", "maxContextCharacters", "captureMode", "trialMode", "trialId",
    }
    missing_config = sorted(k for k in required if k not in cfg)
    trial_id_matches = cfg.get("trialId") == binding.trial_id
    missing_denies = sorted(forbidden - trial_deny)
    stale_tools = sorted(tool_names & STALE_NOLLM_TOOLS)
    mutation_tools = sorted(tool_names & MUTATION_TOOLS)
    disabled_issues = _disabled_entry_config_issues(config)
    ok = (
        slots.get("memory") == "nollm"
        and nollm_entry.get("enabled") is True
        and not stale_tools
        and not mutation_tools
        and not disabled_issues
        and isinstance(trial_agent, dict)
        and not trial_exposed
        and not missing_denies
        and not missing_config
        and trial_id_matches
        and trial_agent.get("contextInjection") == "never"
        and (trial_agent.get("memorySearch") or {}).get("provider") == "none"
    )
    return {
        "ok": ok,
        "memory_slot": slots.get("memory"),
        "nollm_enabled": nollm_entry.get("enabled"),
        "stale_nollm_tools": stale_tools,
        "mutation_tools": mutation_tools,
        "disabled_entry_config_issues": disabled_issues,
        "complete_config_missing_keys": missing_config,
        "trial_id_matches_binding": trial_id_matches,
        "configured_trial_id_sha256": hashlib.sha256(str(cfg.get("trialId", "")).encode("utf-8")).hexdigest() if cfg.get("trialId") else None,
        "target_agent_id": binding.target_agent_id,
        "trial_agent_present": isinstance(trial_agent, dict),
        "trial_agent_exposed_forbidden_tools": trial_exposed,
        "trial_agent_missing_denies": missing_denies,
    }


def _configure_active_trial(config: dict[str, Any], binding: TargetBinding) -> None:
    plugins = config.setdefault("plugins", {})
    entries = plugins.setdefault("entries", {})
    slots = plugins.setdefault("slots", {})
    slots["memory"] = "nollm"
    nollm_entry = entries.setdefault("nollm", {})
    nollm_entry["enabled"] = True
    nollm_entry["config"] = {
        "pythonExecutable": _posix(binding.python_executable),
        "pythonArgs": [],
        "nollmRepoRoot": _posix(binding.repo_root),
        "workspaceRoot": _posix(binding.workspace),
        "nativeStoreRoot": _posix(binding.workspace / ".nollm-memory" / "native-companion-v1"),
        "trialRoot": _posix(binding.workspace / ".nollm-memory" / "active-trials"),
        "commandTimeoutMs": 15000,
        "maxFacts": 4,
        "maxContextCharacters": 1400,
        "captureMode": "deterministic_explicit_v1",
        "trialMode": "active_empirical_v1",
        "trialId": binding.trial_id,
    }
    nollm_entry.setdefault("hooks", {})["allowConversationAccess"] = True
    for name in ("nollm-memory-companion", "active-memory", "memory-core"):
        entry = entries.setdefault(name, {})
        if isinstance(entry, dict):
            entry.clear()
            entry["enabled"] = False
    _remove_stale_tools(config)
    agents = config.setdefault("agents", {})
    agent_list = agents.setdefault("list", [])
    agent = _trial_agent(config, binding.target_agent_id)
    if agent is None:
        raise RuntimeError(f"target_agent_unresolved: {binding.target_agent_id}")
    agent.update({
        "id": binding.target_agent_id,
        "name": binding.target_agent_id,
        "workspace": str(binding.workspace),
        "bootstrapMaxChars": 1,
        "bootstrapTotalMaxChars": 1,
        "contextInjection": "never",
        "memorySearch": {"provider": "none", "fallback": "none"},
        "tools": {"profile": "minimal", "alsoAllow": [], "deny": sorted(MUTATION_TOOLS | LEGACY_MEMORY_TOOLS | STALE_NOLLM_TOOLS)},
    })


def _backup_path(binding: TargetBinding) -> Path:
    return binding.out / "private" / "openclaw-config.backup.json"


def _ensure_private_backup(binding: TargetBinding) -> Path:
    backup = _backup_path(binding)
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(binding.config, backup)
    return backup


def _sidecar_probe(binding: TargetBinding, payload: dict[str, Any]) -> dict[str, Any]:
    script = binding.repo_root / "reference" / "python" / "scripts" / "run_openclaw_nollm_active_memory.py"
    native = binding.workspace / ".nollm-memory" / "native-companion-v1"
    trial = binding.workspace / ".nollm-memory" / "active-trials"
    proc = subprocess.run(
        [str(binding.python_executable), str(script), "--native-store-root", str(native), "--trial-root", str(trial)],
        input=json.dumps(payload, ensure_ascii=False, sort_keys=True),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(binding.out),
        timeout=30,
        shell=False,
    )
    parsed = None
    try:
        parsed = json.loads(proc.stdout)
    except Exception:
        pass
    return {
        "argv_shape": [_redact_text(str(binding.python_executable)), "<active-sidecar-script>", "--native-store-root", "<native-store-root>", "--trial-root", "<trial-root>"],
        "exit_code": proc.returncode,
        "stdout_bytes": len(proc.stdout.encode("utf-8", errors="replace")),
        "stderr_bytes": len(proc.stderr.encode("utf-8", errors="replace")),
        "stdout_tail": _redact_text(proc.stdout)[-4000:],
        "stderr_tail": _redact_text(proc.stderr)[-4000:],
        "parsed_safe_result": _redact_obj(parsed) if isinstance(parsed, dict) else None,
    }


def _plan(binding: TargetBinding) -> dict[str, Any]:
    config_format = _detect_config_format(binding.config)
    version = _run_bound(binding, binding.argv("--version"), timeout=30)
    config_help = _run_bound(binding, binding.argv("config", "--help"), timeout=30)
    plugins_help = _run_bound(binding, binding.argv("plugins", "--help"), timeout=30)
    agent_help = _run_bound(binding, binding.argv("agent", "--help"), timeout=30)
    gateway_help = _run_bound(binding, binding.argv("gateway", "--help"), timeout=30)
    binding_probe = _config_binding_probe(binding)
    plugin_route = _discover_plugin_route(plugins_help.get("stdout_tail", ""))
    legacy_routes = {
        "config_binding": "supported" if binding_probe["ok"] else "unavailable",
        "config_validate": "supported" if "validate" in config_help.get("stdout_tail", "") else "unavailable",
        "runtime_inspect_route": "supported" if "inspect" in plugins_help.get("stdout_tail", "") else "unavailable",
        "memory_owner_route": "supported" if "inspect" in plugins_help.get("stdout_tail", "") else "unavailable",
        "tool_catalog_route": "supported" if "--json" in agent_help.get("stdout_tail", "") else "unavailable",
        "provider_build": "supported" if (binding.repo_root / "integrations" / "openclaw" / "nollm-memory-provider" / "package.json").exists() else "unavailable",
        "provider_link_or_refresh": "supported" if plugin_route else "unavailable",
        "real_turn": "supported" if "--message" in agent_help.get("stdout_tail", "") and "--json" in agent_help.get("stdout_tail", "") else "unavailable",
        "gateway_reload": "supported" if "restart" in gateway_help.get("stdout_tail", "") else "unavailable",
        "tool_catalog": "supported",
    }
    operation_routes = {
        "operation_private_config": "supported" if "--config" in agent_help.get("stdout_tail", "") else "unavailable",
        "operation_private_workspace": "supported" if "--workspace" in agent_help.get("stdout_tail", "") else "unavailable",
        "operation_private_native_store": "supported",
        "operation_private_active_trials": "supported",
        "operation_private_provider_payload": "unavailable",
        "operation_local_plugin_registry": "unavailable",
        "operation_local_gateway_or_process": "unavailable",
        "shared_mutation_fallback": "forbidden",
    }
    required = [
        "operation_private_config",
        "operation_private_workspace",
        "operation_private_native_store",
        "operation_private_active_trials",
        "operation_private_provider_payload",
        "operation_local_plugin_registry",
        "operation_local_gateway_or_process",
    ]
    ok = (
        config_format["ok"]
        and version["exit_code"] == 0
        and all(operation_routes[k] == "supported" for k in required)
        and operation_routes["shared_mutation_fallback"] == "forbidden"
    )
    block_reason = None if ok else "operation_isolation_route_unavailable"
    return {
        "schema": "nollm.w2_05.target_capability_plan.v1",
        "ok": ok,
        "created_at": _now(),
        "binding": binding.redacted(),
        "config_format": config_format,
        "routes": {**legacy_routes, **operation_routes, "real_turn": legacy_routes["real_turn"]},
        "legacy_shared_routes_observed_only": legacy_routes,
        "operation_isolation_routes": operation_routes,
        "required_routes": required,
        "block_reason": block_reason,
        "version": version,
        "binding_probe": binding_probe,
        "plugin_route": plugin_route or None,
    }


def _config_binding_probe(binding: TargetBinding) -> dict[str, Any]:
    probe_dir = binding.out / "binding-probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    invalid = probe_dir / "invalid-openclaw.json"
    invalid.write_text("{ invalid json", encoding="utf-8")
    invalid_binding = TargetBinding(binding.openclaw_bin, invalid, binding.profile, binding.workspace, binding.repo_root, binding.python_executable, binding.out, binding.target_agent_id, binding.trial_id)
    invalid_result = _run_bound(invalid_binding, invalid_binding.argv("config", "validate"), timeout=60)
    real_result = _run_bound(binding, binding.argv("config", "validate"), timeout=60)
    return {
        "schema": "nollm.w2_03r.config_binding_probe.v1",
        "ok": invalid_result["exit_code"] != 0 and real_result["exit_code"] == 0,
        "invalid_fixture_exit_code": invalid_result["exit_code"],
        "real_config_exit_code": real_result["exit_code"],
        "binding_mode": binding.redacted()["binding_mode"],
    }


def _discover_plugin_route(help_text: str) -> str | None:
    lowered = help_text.lower()
    if "install" in lowered:
        return "install"
    if "link" in lowered:
        return "link"
    if "refresh" in lowered:
        return "refresh"
    return None


def _collect_log_window() -> tuple[str, str]:
    log_dir = Path.home() / "AppData" / "Local" / "Temp" / "openclaw"
    if not log_dir.exists():
        return "", "log directory unavailable"
    files = sorted(log_dir.glob("openclaw-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return "", "log file unavailable"
    lines = files[0].read_text(encoding="utf-8", errors="replace").splitlines()
    matches = [i for i, line in enumerate(lines) if "Nollm active prepare failed" in line or ("Nollm active" in line and "failed" in line.lower())]
    if not matches:
        return "\n".join(lines[-300:]), "no active failure signature found"
    chunks: list[str] = []
    for idx in matches[-3:]:
        chunks.extend(lines[max(0, idx - 300):min(len(lines), idx + 301)])
    return "\n".join(chunks), "matched active failure signature"


def _diagnose(binding: TargetBinding) -> dict[str, Any]:
    diag_id = _stamp()
    diag = binding.out / "diagnostics" / diag_id
    diag.mkdir(parents=True, exist_ok=True)
    version = _run_bound(binding, binding.argv("--version"), timeout=30)
    status = _run_bound(binding, binding.argv("status"), timeout=60)
    plugins = _run_bound(binding, binding.argv("plugins", "list"), timeout=60)
    pyprobe = _run_bound(binding, [str(binding.python_executable), "-c", "import sys,json; print(json.dumps({'executable': sys.executable, 'version': sys.version}))"], timeout=30)
    sidecar_status = _sidecar_probe(binding, {"command": "active-status", "schema": ACTIVE_STATUS_SCHEMA})
    sidecar_prepare = _sidecar_probe(binding, {"command": "active-prepare", "schema": ACTIVE_PREPARE_SCHEMA, "query": "明天东京天气如何？", "budget": {"max_facts": 4, "max_context_characters": 1400}})
    log_window, log_note = _collect_log_window()
    config = _read_json(binding.config)
    relevant_config = {
        "plugins": {"slots": (config.get("plugins") or {}).get("slots"), "entries": {k: ((config.get("plugins") or {}).get("entries") or {}).get(k) for k in ["nollm", "memory-core", "active-memory", "nollm-memory-companion"]}},
        "tools": config.get("tools"),
        "agents": {"list": [a for a in ((config.get("agents") or {}).get("list") or []) if isinstance(a, dict) and a.get("id") == binding.target_agent_id]},
    }
    traceback_text = "\n".join(line for line in log_window.splitlines() if "Traceback" in line or "Nollm active prepare failed" in line) or "No active traceback found in bounded log window."
    minimal = {
        "schema": "nollm.w2_03.minimal_reproduction.v1",
        "classification": "none_observed" if sidecar_status["exit_code"] == 0 and sidecar_prepare["exit_code"] == 0 else "sidecar_or_json_protocol",
        "sidecar_status_exit_code": sidecar_status["exit_code"],
        "sidecar_prepare_exit_code": sidecar_prepare["exit_code"],
        "smallest_command": sidecar_prepare["argv_shape"],
    }
    _write_json(diag / "manifest.json", {"schema": "nollm.w2_03.diagnostic_manifest.v1", "created_at": _now(), "diagnostic_id": diag_id, "binding": binding.redacted(), "log_note": log_note})
    _write_json(diag / "runtime-versions.json", {"schema": "nollm.w2_03.runtime_versions.v1", "openclaw": version, "node": _run_bound(binding, ["node", "--version"], timeout=30), "python": pyprobe})
    _write_json(diag / "target-binding.json", {"schema": "nollm.w2_03.target_binding.v1", "binding": binding.redacted()})
    _write_json(diag / "effective-config-redacted.json", _redact_obj(relevant_config))
    _write_json(diag / "sidecar-direct-status.json", sidecar_status)
    _write_json(diag / "sidecar-direct-prepare.json", sidecar_prepare)
    _write_json(diag / "minimal-reproduction.json", minimal)
    _write_json(diag / "redaction-report.json", {"schema": "nollm.w2_03.redaction_report.v1", "home_path_redacted": True, "secret_patterns_redacted": True})
    (diag / "gateway-log-window.txt").write_text(_redact_text(log_window), encoding="utf-8")
    (diag / "full-traceback.txt").write_text(_redact_text(traceback_text), encoding="utf-8")
    (diag / "plugin-runtime-inspect.txt").write_text(_redact_text(plugins.get("stdout_tail", "") + "\n" + plugins.get("stderr_tail", "")), encoding="utf-8")
    (diag / "tool-catalog-inspect.txt").write_text("Tool catalog is verified through real trial turn systemPromptReport.tools.entries when trial runs.\n", encoding="utf-8")
    with (diag / "command-results.jsonl").open("w", encoding="utf-8") as handle:
        for receipt in (version, status, plugins, pyprobe):
            handle.write(json.dumps(_redact_obj(receipt), ensure_ascii=False, sort_keys=True) + "\n")
    share_zip = binding.out / "diagnostics" / f"{diag_id}-share-sanitized.zip"
    with zipfile.ZipFile(share_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(diag.iterdir()):
            if path.is_file() and path.name != "command-results.jsonl":
                zf.write(path, path.name)
    result = {"schema": "nollm.w2_03.diagnose_result.v1", "ok": True, "private_capsule": str(diag), "sanitized_share_capsule": str(share_zip), "minimal_reproduction": minimal}
    _write_json(binding.out / "diagnose.json", result)
    return result


def _backup_path(binding: TargetBinding) -> Path:
    return binding.out / "private" / "openclaw-config.backup.json"


def _restore_backup(binding: TargetBinding) -> dict[str, Any]:
    backup = _backup_path(binding)
    if not backup.exists():
        return {"ok": False, "error": "backup_missing"}
    backup_hash = _sha256_file(backup)
    tmp = binding.config.with_suffix(binding.config.suffix + ".rollback.tmp")
    shutil.copy2(backup, tmp)
    os.replace(str(tmp), str(binding.config))
    reload_receipt = _run_bound(binding, binding.argv("gateway", "restart"), timeout=120)
    restored_hash = _sha256_file(binding.config)
    validate = _run_bound(binding, binding.argv("config", "validate"), timeout=60)
    return {
        "ok": reload_receipt["exit_code"] == 0 and validate["exit_code"] == 0 and restored_hash == backup_hash,
        "config_restored_byte_identical": restored_hash == backup_hash,
        "restored_config_sha256": restored_hash,
        "backup_sha256": backup_hash,
        "reload": reload_receipt,
        "validate": validate,
    }


def _runtime_assert(binding: TargetBinding) -> dict[str, Any]:
    config_assert = _config_assertions(_read_json(binding.config), binding)
    plugin_receipt = _run_bound(binding, binding.argv("plugins", "inspect", "nollm"), timeout=60)
    plugin_text = "\n".join([plugin_receipt.get("stdout_tail", ""), plugin_receipt.get("stderr_tail", "")])
    loaded_nollm = plugin_receipt["exit_code"] == 0 and re.search(r"\bid:\s*nollm\b", plugin_text, flags=re.I) and re.search(r"\bStatus:\s*loaded\b", plugin_text, flags=re.I)
    provider_files = [
        binding.repo_root / "integrations" / "openclaw" / "nollm-memory-provider" / "dist" / "index.js",
        binding.repo_root / "integrations" / "openclaw" / "nollm-memory-provider" / "openclaw.plugin.json",
        binding.repo_root / "integrations" / "openclaw" / "nollm-memory-provider" / "package.json",
    ]
    provider_hash = hashlib.sha256()
    provider_hash_count = 0
    for path in provider_files:
        if path.exists():
            provider_hash.update(path.name.encode("utf-8"))
            provider_hash.update(path.read_bytes())
            provider_hash_count += 1
    active_status = _sidecar_probe(binding, {"command": "active-status", "schema": ACTIVE_STATUS_SCHEMA})
    turn = _run_agent_turn(binding, f"w2-04-runtime-assert-{_stamp()}", "只回答 OK-W2-04-RUNTIME。")
    catalog_safe, catalog_names, catalog_status = _tool_catalog_safe(turn)
    runtime = {
        "schema": "nollm.w2_04.runtime_proof.v1",
        "config_assertions": config_assert,
        "runtime_assertions": {
            "status": "observed" if loaded_nollm else "failed",
            "loaded_plugin_ids": ["nollm"] if loaded_nollm else [],
            "loaded_nollm_provider": bool(loaded_nollm),
            "selected_memory_owner": "nollm" if config_assert.get("memory_slot") == "nollm" and loaded_nollm else None,
            "memory_core_selected": False,
            "active_memory_selected": False,
            "provider_build_identity": provider_hash.hexdigest() if provider_hash_count else None,
            "provider_build_file_count": provider_hash_count,
            "source": "target runtime inspect route plus config memory slot",
            "plugin_inspect_exit_code": plugin_receipt["exit_code"],
        },
        "sidecar_health": {
            "active_status_exit_code": active_status["exit_code"],
            "active_status_ok": bool((active_status.get("parsed_safe_result") or {}).get("ok")),
        },
        "turn_assertions": {
            "status": "observed" if turn["exit_code"] == 0 and catalog_status == "observed" else "failed",
            "target_agent_id": binding.target_agent_id,
            "tool_catalog_status": catalog_status,
            "visible_tools": catalog_names,
            "target_turn_exit_code": turn["exit_code"],
            "primary_visible_nollm_tools": sorted(set(catalog_names) & (STALE_NOLLM_TOOLS | LEGACY_MEMORY_TOOLS)),
        },
    }
    runtime["ok"] = (
        config_assert["ok"]
        and bool(loaded_nollm)
        and runtime["runtime_assertions"]["selected_memory_owner"] == "nollm"
        and runtime["sidecar_health"]["active_status_ok"]
        and turn["exit_code"] == 0
        and catalog_safe
        and not runtime["turn_assertions"]["primary_visible_nollm_tools"]
    )
    return runtime


def _cmd_plan(args: argparse.Namespace) -> int:
    binding = TargetBinding.from_args(args)
    plan = _plan(binding)
    _write_json(binding.out / "target-capability-plan.json", plan)
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0 if plan["ok"] else 2


def _cmd_diagnose(args: argparse.Namespace) -> int:
    result = _diagnose(TargetBinding.from_args(args))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _cmd_snapshot(args: argparse.Namespace) -> int:
    binding = TargetBinding.from_args(args)
    backup = _ensure_private_backup(binding)
    config = _read_json(binding.config)
    report = {"schema": "nollm.w2_04.snapshot.v1", "ok": True, "created_at": _now(), "config_sha256": _sha256_file(binding.config), "legacy_sources": _legacy_hashes(binding.workspace), "config_assertions": _config_assertions(config, binding), "private_backup": str(backup)}
    _write_json(binding.out / "snapshot.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _cmd_apply(args: argparse.Namespace) -> int:
    binding = TargetBinding.from_args(args)
    plan = _plan(binding)
    _write_json(binding.out / "target-capability-plan.json", plan)
    op = create_operation(binding.out, getattr(args, "operation_id", None), binding.redacted())
    op_root = Path(op["operation_root"])
    _write_json(op_root / "receipts" / "target-capability-plan.json", plan)
    config_copy = op_root / "private" / "openclaw" / binding.config.name
    shutil.copy2(binding.config, config_copy)
    _write_json(op_root / "private" / "openclaw" / "source-config-reference.json", {
        "schema": "nollm.w2_05.source_config_reference.v1",
        "source_config_sha256": _sha256_file(binding.config),
        "source_config_path_redacted": _redact_text(str(binding.config)),
        "operation_private_copy": str(config_copy),
    })
    if not plan["ok"]:
        set_operation_state(op_root, "blocked_pre_mutation", "operation_isolation_route_unavailable", {
            "shared_mutation_fallback": "forbidden",
            "unavailable_routes": {
                k: v for k, v in (plan.get("operation_isolation_routes") or {}).items() if v != "supported"
            },
        })
        result = {
            "schema": "nollm.w2_05.apply_result.v1",
            "ok": False,
            "operation_id": op["operation_id"],
            "operation_root": op["operation_root"],
            "state": "blocked_pre_mutation",
            "reason": "operation_isolation_route_unavailable",
            "live_validation_blocked": True,
            "shared_mutation_attempted": False,
            "apply_rolled_back": False,
            "plan": plan,
        }
        _write_json(binding.out / "apply.json", result)
        _write_json(op_root / "apply.json", result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2
    quarantine_operation(op_root, "operation_local_runtime_route_not_implemented", {"plan_ok": True})
    result = {
        "schema": "nollm.w2_05.apply_result.v1",
        "ok": False,
        "operation_id": op["operation_id"],
        "operation_root": op["operation_root"],
        "state": "manual_repair_required",
        "reason": "operation_local_runtime_route_not_implemented",
        "shared_mutation_attempted": False,
        "apply_rolled_back": False,
    }
    _write_json(binding.out / "apply.json", result)
    _write_json(op_root / "apply.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2


def _cmd_assert_runtime(args: argparse.Namespace) -> int:
    binding = TargetBinding.from_args(args)
    runtime = _runtime_assert(binding)
    _write_json(binding.out / "runtime-assertions.json", runtime)
    print(json.dumps(runtime, indent=2, sort_keys=True))
    return 0 if runtime["ok"] else 1


def _run_agent_turn(binding: TargetBinding, session: str, message: str) -> dict[str, Any]:
    return _run_bound(binding, binding.argv("agent", "--agent", binding.target_agent_id, "--session-key", f"agent:{binding.target_agent_id}:{session}", "--message", message, "--json", "--timeout", "180"), timeout=220)


def _tool_catalog_safe(turn: dict[str, Any]) -> tuple[bool, list[str], str]:
    parsed = turn.get("parsed_safe_result") if isinstance(turn.get("parsed_safe_result"), dict) else None
    report = (((parsed or {}).get("result") or {}).get("meta") or {}).get("systemPromptReport")
    if not isinstance(report, dict):
        return False, [], "missing_system_prompt_report"
    tools = report.get("tools")
    if not isinstance(tools, dict):
        return False, [], "missing_tools"
    entries = tools.get("entries")
    if not isinstance(entries, list):
        return False, [], "missing_or_malformed_entries"
    names = sorted(e.get("name") for e in entries if isinstance(e, dict) and isinstance(e.get("name"), str))
    forbidden = set(names) & (MUTATION_TOOLS | LEGACY_MEMORY_TOOLS | STALE_NOLLM_TOOLS | {"file_fetch", "file_write", "dir_fetch", "dir_list", "read"})
    return not forbidden, names, "observed"


def _final_answer_text(turn: dict[str, Any]) -> dict[str, Any]:
    parsed = turn.get("parsed_safe_result") if isinstance(turn.get("parsed_safe_result"), dict) else None
    result = parsed.get("result") if isinstance(parsed, dict) and isinstance(parsed.get("result"), dict) else {}
    meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}
    candidates = [
        meta.get("finalAssistantVisibleText"),
        result.get("finalAssistantVisibleText"),
        result.get("text"),
        result.get("content"),
    ]
    payloads = result.get("payloads")
    if isinstance(payloads, list):
        for item in payloads:
            if isinstance(item, dict):
                candidates.extend([item.get("text"), item.get("content")])
    for value in candidates:
        if isinstance(value, str) and value.strip():
            text = value.strip()
            return {"ok": True, "text": text, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    return {"ok": False, "text": "", "sha256": None}


def _active_report(binding: TargetBinding) -> dict[str, Any]:
    receipt = _sidecar_probe(binding, {"command": "active-trial-report", "schema": ACTIVE_TRIAL_REPORT_SCHEMA, "trial_id": binding.trial_id})
    parsed = receipt.get("parsed_safe_result") if isinstance(receipt.get("parsed_safe_result"), dict) else {}
    return {"receipt": receipt, "parsed": parsed if isinstance(parsed, dict) else {}}


def _active_status(binding: TargetBinding) -> dict[str, Any]:
    receipt = _sidecar_probe(binding, {"command": "active-status", "schema": ACTIVE_STATUS_SCHEMA})
    parsed = receipt.get("parsed_safe_result") if isinstance(receipt.get("parsed_safe_result"), dict) else {}
    return {"receipt": receipt, "parsed": parsed if isinstance(parsed, dict) else {}}


def _active_prepare_contains(binding: TargetBinding, query: str, expected: str) -> dict[str, Any]:
    receipt = _sidecar_probe(binding, {"command": "active-prepare", "schema": ACTIVE_PREPARE_SCHEMA, "query": query, "trial_id": binding.trial_id})
    parsed = receipt.get("parsed_safe_result") if isinstance(receipt.get("parsed_safe_result"), dict) else {}
    facts = (((parsed.get("context") if isinstance(parsed, dict) else {}) or {}).get("facts") or [])
    claims = [str(f.get("claim", "")) for f in facts if isinstance(f, dict)]
    found = any(expected in claim for claim in claims)
    return {
        "ok": receipt["exit_code"] == 0 and bool(parsed.get("ok")) and found,
        "exit_code": receipt["exit_code"],
        "expected_sha256": hashlib.sha256(expected.encode("utf-8")).hexdigest(),
        "fact_count": len(claims),
        "matched": found,
        "receipt": receipt,
    }


def _cmd_trial(args: argparse.Namespace) -> int:
    binding = TargetBinding.from_args(args)
    operation_id = getattr(args, "operation_id", None)
    plan = _plan(binding)
    if not operation_id:
        result = {
            "schema": "nollm.w2_05.trial_result.v1",
            "ok": False,
            "state": "blocked_pre_mutation",
            "reason": "operation_id_required_for_operation_isolated_trial",
            "shared_turn_attempted": False,
            "automatic_rollback": None,
            "plan": plan,
        }
        _write_json(binding.out / "trial.json", result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2
    validate_operation_id(operation_id)
    op_root = operation_root(binding.out, operation_id)
    if not op_root.exists():
        result = {
            "schema": "nollm.w2_05.trial_result.v1",
            "ok": False,
            "operation_id": operation_id,
            "state": "blocked_pre_mutation",
            "reason": "operation_not_prepared",
            "shared_turn_attempted": False,
            "automatic_rollback": None,
        }
        _write_json(binding.out / "trial.json", result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2
    set_operation_state(op_root, "blocked_pre_mutation", "operation_local_runtime_route_unavailable_for_trial", {
        "shared_turn_attempted": False,
        "shared_mutation_fallback": "forbidden",
    })
    result = {
        "schema": "nollm.w2_05.trial_result.v1",
        "ok": False,
        "operation_id": operation_id,
        "operation_root": str(op_root),
        "state": "blocked_pre_mutation",
        "reason": "operation_isolation_route_unavailable",
        "shared_turn_attempted": False,
        "automatic_rollback": None,
        "plan": plan,
    }
    _write_json(binding.out / "trial.json", result)
    _write_json(op_root / "trial.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2


def _cmd_trial_legacy_disabled(args: argparse.Namespace) -> int:
    binding = TargetBinding.from_args(args)
    before = _legacy_hashes(binding.workspace)
    status_before = _active_status(binding)
    report_before = _active_report(binding)
    stages = [
        ("temporal-no-save", "2026年6月28日，用户报告昆明当天下雨。只回答 OK-W2-04-TEMPORAL。"),
        ("capture-identity", "请记住：我的 W2-04 身份 marker 是 LANTERN-CEDAR-71。只回答 OK-W2-04-CAPTURE-IDENTITY。"),
        ("capture-preference", "请记住：我的 W2-04 标签颜色 marker 是 MINT-ORBIT-82。只回答 OK-W2-04-CAPTURE-PREFERENCE。"),
        ("capture-release", "请记住：我的 W2-04 发布窗口 marker 是 GRANITE-EMBER-93。只回答 OK-W2-04-CAPTURE-RELEASE。"),
        ("capture-rain-note", "请记住：2026年6月28日，用户报告昆明当天下雨。只回答 OK-W2-04-CAPTURE-RAIN-NOTE。"),
        ("recall-identity", "我的 W2-04 身份 marker 是什么？只回答 marker 本身。"),
        ("recall-preference", "我的 W2-04 标签颜色 marker 是什么？只回答 marker 本身。"),
        ("recall-release", "我的 W2-04 发布窗口 marker 是什么？只回答 marker 本身。"),
        ("recall-rain-note", "用户报告昆明当天下雨的日期和内容是什么？只回答已保存的完整原句。"),
        ("weather-no-match", "明天东京天气如何？不要使用工具。简短回答。"),
    ]
    expected = {
        "recall-identity": "LANTERN-CEDAR-71",
        "recall-preference": "MINT-ORBIT-82",
        "recall-release": "GRANITE-EMBER-93",
        "recall-rain-note": "2026年6月28日，用户报告昆明当天下雨。",
    }
    receipts = []
    ok = True
    failures: list[str] = []
    observed_tools: list[str] = []
    for name, message in stages:
        if name.startswith("recall-"):
            prepare = _active_prepare_contains(binding, message, expected[name])
            receipts.append({"stage": f"{name}-active-prepare", "receipt": _redact_obj(prepare)})
            if not prepare["ok"]:
                ok = False
                failures.append(f"active_prepare_missing_expected_marker:{name}")
                break
        pre_status = _active_status(binding)
        pre_report = _active_report(binding)
        receipt = _run_agent_turn(binding, f"w2-04-{name}-{_stamp()}", message)
        answer = _final_answer_text(receipt)
        post_status = _active_status(binding)
        post_report = _active_report(binding)
        receipts.append({
            "stage": name,
            "final_answer": answer,
            "native_record_count_before": (pre_status.get("parsed") or {}).get("native_record_count"),
            "native_record_count_after": (post_status.get("parsed") or {}).get("native_record_count"),
            "promotion_total_before": (pre_report.get("parsed") or {}).get("promotion_total"),
            "promotion_total_after": (post_report.get("parsed") or {}).get("promotion_total"),
            "receipt": receipt,
        })
        safe, tools, catalog_status = _tool_catalog_safe(receipt)
        observed_tools = tools
        if not safe:
            ok = False
            failures.append(f"unsafe_or_missing_tool_catalog:{name}:{catalog_status}")
            break
        if not answer["ok"]:
            ok = False; failures.append(f"final_answer_unavailable:{name}")
        visible_text = answer.get("text", "")
        if name == "temporal-no-save":
            if ("已记住" in visible_text or "所在地" in visible_text):
                ok = False; failures.append("temporal_report_false_persistence_or_location_inference")
            if (pre_status.get("parsed") or {}).get("native_record_count") != (post_status.get("parsed") or {}).get("native_record_count"):
                ok = False; failures.append("temporal_native_record_delta")
            if (pre_report.get("parsed") or {}).get("promotion_total") != (post_report.get("parsed") or {}).get("promotion_total"):
                ok = False; failures.append("temporal_promotion_delta")
        if name in expected and visible_text.strip() != expected[name]:
            ok = False; failures.append(f"{name}_final_answer_not_exact_expected")
        if name == "weather-no-match" and any(m in visible_text for m in expected.values()):
            ok = False; failures.append("weather_query_injected_w2_04_fact")
        if _legacy_hashes(binding.workspace) != before:
            ok = False
            failures.append("legacy_source_mutation")
            break
        if not ok:
            break
    automatic_rollback = None
    if not ok:
        automatic_rollback = _restore_backup(binding)
        receipts.append({"stage": "automatic-rollback", "receipt": automatic_rollback})
    active_report = _active_report(binding)
    active_result = active_report.get("parsed") or {}
    if ok and not active_result.get("ok"):
        ok = False
        failures.append("active_trial_report_unavailable")
    report = {
        "schema": "nollm.w2_04.trial_result.v1",
        "ok": ok,
        "created_at": _now(),
        "trial_id": binding.trial_id,
        "failures": failures,
        "observed_trial_tool_catalog": observed_tools,
        "status_before": _redact_obj(status_before.get("parsed") or {}),
        "report_before": _redact_obj(report_before.get("parsed") or {}),
        "active_trial_report": _redact_obj(active_result),
        "active_trial_report_exit_code": active_report["receipt"]["exit_code"],
        "automatic_rollback": automatic_rollback,
        "legacy_sources_unchanged": _legacy_hashes(binding.workspace) == before,
        "receipts": receipts,
    }
    _write_json(binding.out / "trial.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ok else 1


def _cmd_rollback(args: argparse.Namespace) -> int:
    binding = TargetBinding.from_args(args)
    operation_id = getattr(args, "operation_id", None)
    report = {
        "schema": "nollm.w2_05.rollback_result.v1",
        "ok": False,
        "created_at": _now(),
        "operation_id": operation_id,
        "state": "manual_repair_required" if operation_id else "blocked_pre_mutation",
        "reason": "shared_environment_rollback_forbidden_in_w2_05",
        "shared_mutation_attempted": False,
        "legacy_sources_unchanged": True,
    }
    if operation_id:
        op_root = operation_root(binding.out, validate_operation_id(operation_id))
        if op_root.exists():
            set_operation_state(op_root, "manual_repair_required", "rollback_requires_manual_operation_resolution", {})
            _write_json(op_root / "rollback.json", report)
    _write_json(binding.out / "rollback.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2


def _cmd_inspect(args: argparse.Namespace) -> int:
    binding = TargetBinding.from_args(args)
    operation_id = getattr(args, "operation_id", None)
    if not operation_id:
        result = {"schema": "nollm.w2_05.inspect_result.v1", "ok": False, "error": "operation_id_required"}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2
    op_root = operation_root(binding.out, validate_operation_id(operation_id))
    manifest_path = op_root / "operation.json"
    if not manifest_path.exists():
        result = {"schema": "nollm.w2_05.inspect_result.v1", "ok": False, "operation_id": operation_id, "error": "operation_not_found"}
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2
    ledger_path = op_root / "operation-ledger.jsonl"
    ledger = []
    if ledger_path.exists():
        ledger = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = {
        "schema": "nollm.w2_05.inspect_result.v1",
        "ok": True,
        "operation_id": operation_id,
        "operation_root": str(op_root),
        "manifest": _read_json(manifest_path),
        "ledger_event_count": len(ledger),
        "latest_state": ledger[-1]["state"] if ledger else None,
        "quarantined": (op_root / "QUARANTINED").exists(),
    }
    _write_json(binding.out / "inspect.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _cmd_hash_legacy(args: argparse.Namespace) -> int:
    binding = TargetBinding.from_args(args)
    report = {"schema": "nollm.w2_04.legacy_hashes.v1", "ok": True, "created_at": _now(), "stage": args.stage, "legacy_sources": _legacy_hashes(binding.workspace)}
    _write_json(binding.out / f"legacy-hashes-{args.stage}.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    binding = TargetBinding.from_args(args)
    files = {path.name: _sha256_file(path) for path in sorted(binding.out.glob("*.json"))}
    operations = []
    for op_path in sorted((binding.out / "operations").glob("w2-05-*")) if (binding.out / "operations").exists() else []:
        if (op_path / "operation.json").exists():
            operations.append(_read_json(op_path / "operation.json"))
    report = {"schema": "nollm.w2_05.report_manifest.v1", "ok": True, "created_at": _now(), "artifact_hashes": files, "operations": operations}
    _write_json(binding.out / "report-manifest.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="W2-05 operation-isolated Nollm active-memory forensic controller.")
    parser.add_argument("command", choices=["plan", "diagnose", "snapshot", "apply", "assert-runtime", "trial", "rollback", "reapply", "inspect", "report", "hash-legacy"])
    parser.add_argument("--openclaw-bin", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--python-executable", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--target-agent-id", required=True)
    parser.add_argument("--trial-id")
    parser.add_argument("--operation-id")
    parser.add_argument("--stage", default="manual")
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            return _cmd_plan(args)
        if args.command == "diagnose":
            return _cmd_diagnose(args)
        if args.command == "snapshot":
            return _cmd_snapshot(args)
        if args.command == "apply":
            return _cmd_apply(args)
        if args.command == "reapply":
            return _cmd_rollback(args)
        if args.command == "assert-runtime":
            return _cmd_assert_runtime(args)
        if args.command == "trial":
            return _cmd_trial(args)
        if args.command == "rollback":
            return _cmd_rollback(args)
        if args.command == "inspect":
            return _cmd_inspect(args)
        if args.command == "hash-legacy":
            return _cmd_hash_legacy(args)
        if args.command == "report":
            return _cmd_report(args)
    except Exception as exc:
        print(json.dumps({"schema": "nollm.w2_05.controller_error.v1", "ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
