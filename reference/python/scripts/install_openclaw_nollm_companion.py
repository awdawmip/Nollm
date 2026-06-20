from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any
import time


PLUGIN_ID = "nollm-memory-companion"
READ_TOOLS = ["nollm_memory_search", "nollm_memory_get", "nollm_memory_status"]
WRITE_TOOL = "nollm_memory_write_candidate"
FORBIDDEN_SEMANTICS = {
    "memory_slot_replacement": False,
    "kind_memory": False,
    "real_llm_call": False,
    "auto_memory_write": False,
    "drift_class_trust_mapping": False,
    "hard_drift_rejection": False,
}
INSTALL_TIMEOUT_SECONDS = 60
CONFIG_TIMEOUT_SECONDS = 60
INSPECT_TIMEOUT_SECONDS = 30
READINESS_DEADLINE_SECONDS = 20
READINESS_POLL_INTERVAL_SECONDS = 2
SOURCE_MEMORY_PATTERNS = ["MEMORY.md", "DREAMS.md", "memory/**/*.md"]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_initial_report(args)
    try:
        run_installer(args, report)
    except InstallerError as exc:
        report["ok"] = False
        report["errors"].append({"code": exc.code, "message": str(exc)})
    except Exception as exc:  # pragma: no cover - defensive final envelope
        report["ok"] = False
        report["errors"].append({"code": "unexpected_error", "message": safe_message(str(exc))})
    finally:
        write_report(report, args)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install/link the Nollm OpenClaw companion tool plugin.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Discover and validate without writing config or installing.")
    mode.add_argument("--apply", action="store_true", help="Apply local OpenClaw integration changes.")
    parser.add_argument("--openclaw-bin", default=None)
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--config-path", default=None)
    parser.add_argument("--plugin-root", default=None)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--no-restart", action="store_true")
    parser.add_argument("--enable-write-candidate", action="store_true")
    parser.add_argument("--probe-query", default="Nollm companion integration status")
    parser.add_argument("--report-path", default=None)
    return parser.parse_args(argv)


def build_initial_report(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "ok": False,
        "mode": "apply" if args.apply else "dry_run",
        "openclaw_version": None,
        "node_version": None,
        "plugin_id": PLUGIN_ID,
        "plugin_root": None,
        "workspace_root": None,
        "config_path": None,
        "plugin_installation": {"attempted": False, "ok": False},
        "config_validation": {"attempted": False, "ok": False},
        "runtime_inspection": {"attempted": False, "ok": False},
        "skill_discovery_or_manifest_check": {"attempted": False, "ok": False},
        "gateway_restart_or_reload": {"attempted": False, "ok": False, "skipped": False},
        "gateway_status": {"attempted": False, "ok": False},
        "sidecar_probe": {"attempted": False, "ok": False},
        "read_tools_visible": [],
        "write_candidate_visible": False,
        "memory_slot_owner": "openclaw-memory-core",
        "forbidden_semantics": dict(FORBIDDEN_SEMANTICS),
        "post_link_readiness": {"attempted": False, "ok": False},
        "post_restart_readiness": {"attempted": False, "ok": False},
        "integration_evidence": {
            "plugin_link_state": None,
            "config_patch_applied": False,
            "runtime_tool_names": [],
            "required_read_tools_visible": False,
            "write_candidate_default_enabled": False,
            "source_memory_hashes_before": {},
            "source_memory_hashes_after": {},
            "source_memory_unchanged": None,
            "sidecar_index_ok": False,
            "sidecar_search_ok": False,
            "sidecar_result_count": 0,
        },
        "errors": [],
    }


def run_installer(args: argparse.Namespace, report: dict[str, Any]) -> None:
    openclaw_bin = args.openclaw_bin or shutil.which("openclaw")
    if not openclaw_bin:
        raise InstallerError("openclaw_not_found", "openclaw executable was not found on PATH.")

    repo_root = Path(args.repo_root).resolve() if args.repo_root else git_repo_root()
    plugin_root = Path(args.plugin_root).resolve() if args.plugin_root else repo_root / "integrations/openclaw/nollm-memory-companion"
    report["plugin_root"] = str(plugin_root)

    node_bin = shutil.which("node")
    if not node_bin:
        raise InstallerError("node_not_found", "node executable was not found on PATH.")
    report["node_version"] = run_capture([node_bin, "--version"], cwd=repo_root).stdout.strip()
    report["openclaw_version"] = run_capture([openclaw_bin, "--version"], cwd=repo_root).stdout.strip()

    config_path = Path(args.config_path).expanduser().resolve() if args.config_path else Path(
        run_capture([openclaw_bin, "config", "file"], cwd=repo_root).stdout.strip()
    ).expanduser().resolve()
    report["config_path"] = str(config_path)
    config_before = read_json_file(config_path)

    workspace_root = Path(args.workspace).resolve() if args.workspace else discover_workspace(openclaw_bin, repo_root)
    report["workspace_root"] = str(workspace_root)
    report["integration_evidence"]["source_memory_hashes_before"] = hash_source_memory_files(workspace_root)

    ensure_plugin_package_ready(openclaw_bin, plugin_root, report)
    patch = build_config_patch(
        config_before=config_before,
        repo_root=repo_root,
        workspace_root=workspace_root,
        enable_write_candidate=args.enable_write_candidate,
    )
    report["config_patch_summary"] = summarize_patch(patch)

    if args.dry_run:
        validate_patch_dry_run(openclaw_bin, repo_root, patch, report)
        report["skill_discovery_or_manifest_check"] = check_skill_manifest(plugin_root)
        report["write_candidate_visible"] = bool(args.enable_write_candidate)
        report["read_tools_visible"] = READ_TOOLS
        finish_source_hash_evidence(workspace_root, report)
        report["ok"] = len(report["errors"]) == 0
        return

    install_plugin(openclaw_bin, plugin_root, repo_root, report)
    apply_config_patch(openclaw_bin, repo_root, patch)
    report["integration_evidence"]["config_patch_applied"] = True
    validate_config(openclaw_bin, repo_root, report)
    if args.no_restart:
        report["gateway_restart_or_reload"] = {"attempted": False, "ok": False, "skipped": True, "reason": "--no-restart"}
    else:
        restart_gateway(openclaw_bin, repo_root, report)
    gateway_status(openclaw_bin, repo_root, report)
    inspect_runtime(openclaw_bin, repo_root, report)
    if not args.no_restart:
        poll_runtime_tools(openclaw_bin, repo_root, plugin_root, report, "post_restart_readiness")
    report["skill_discovery_or_manifest_check"] = check_skill_manifest(plugin_root)
    run_sidecar_probe(repo_root, workspace_root, args.probe_query, report)
    finish_source_hash_evidence(workspace_root, report)
    report["ok"] = len(report["errors"]) == 0 and report["runtime_inspection"].get("ok") is True


def ensure_plugin_package_ready(openclaw_bin: str, plugin_root: Path, report: dict[str, Any]) -> None:
    npm_bin = shutil.which("npm")
    if not npm_bin:
        raise InstallerError("npm_not_found", "npm executable was not found on PATH.")
    run_checked([npm_bin, "run", "plugin:build"], cwd=plugin_root, code="plugin_build_failed")
    run_checked(
        [npm_bin, "run", "build"],
        cwd=plugin_root,
        code="plugin_compile_failed",
    )
    run_checked(
        [openclaw_bin, "plugins", "build", "--entry", "./dist/index.js", "--check"],
        cwd=plugin_root,
        code="plugin_metadata_check_failed",
    )
    run_checked(
        [openclaw_bin, "plugins", "validate", "--entry", "./dist/index.js"],
        cwd=plugin_root,
        code="plugin_validate_failed",
    )
    report["plugin_build_validation"] = {"attempted": True, "ok": True}


def build_config_patch(
    *,
    config_before: dict[str, Any],
    repo_root: Path,
    workspace_root: Path,
    enable_write_candidate: bool,
) -> dict[str, Any]:
    plugin_config = {
        "enabled": True,
        "config": {
            "pythonCommand": "python3",
            "nollmRepoRoot": str(repo_root),
            "workspaceRoot": str(workspace_root),
            "sidecarOutDir": str(workspace_root / ".nollm-memory"),
            "commandTimeoutMs": 15000,
            "maxSearchResults": 5,
        },
    }
    patch: dict[str, Any] = {"plugins": {"entries": {PLUGIN_ID: plugin_config}}}
    existing_tools_allow = get_nested(config_before, ["tools", "allow"])
    if isinstance(existing_tools_allow, list):
        allowed = union_preserve([str(item) for item in existing_tools_allow], READ_TOOLS)
        if enable_write_candidate:
            allowed = union_preserve(allowed, [WRITE_TOOL])
        patch.setdefault("tools", {})["allow"] = allowed
    return patch


def validate_patch_dry_run(openclaw_bin: str, cwd: Path, patch: dict[str, Any], report: dict[str, Any]) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(patch, handle, indent=2, sort_keys=True)
        patch_path = Path(handle.name)
    try:
        run_checked(
            [openclaw_bin, "config", "patch", "--file", str(patch_path), "--dry-run"],
            cwd=cwd,
            code="config_patch_dry_run_failed",
            timeout=CONFIG_TIMEOUT_SECONDS,
        )
        report["config_validation"] = {"attempted": True, "ok": True, "dry_run": True}
    finally:
        patch_path.unlink(missing_ok=True)


def apply_config_patch(openclaw_bin: str, cwd: Path, patch: dict[str, Any]) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(patch, handle, indent=2, sort_keys=True)
        patch_path = Path(handle.name)
    try:
        run_checked(
            [openclaw_bin, "config", "patch", "--file", str(patch_path)],
            cwd=cwd,
            code="config_patch_failed",
            timeout=CONFIG_TIMEOUT_SECONDS,
        )
    finally:
        patch_path.unlink(missing_ok=True)


def install_plugin(openclaw_bin: str, plugin_root: Path, cwd: Path, report: dict[str, Any]) -> None:
    state = inspect_installed_plugin_state(openclaw_bin, cwd, plugin_root)
    if state.get("source_matches") is True and state.get("enabled") is True:
        report["plugin_installation"] = {
            "attempted": False,
            "ok": True,
            "method": "already_linked",
            "source_matches": True,
        }
        report["integration_evidence"]["plugin_link_state"] = "already_linked"
        return
    report["plugin_installation"]["attempted"] = True
    run_checked(
        [openclaw_bin, "plugins", "install", "--link", str(plugin_root)],
        cwd=plugin_root,
        code="plugin_install_failed",
        timeout=INSTALL_TIMEOUT_SECONDS,
    )
    report["plugin_installation"].update({"ok": True, "method": "link", "source_matches": state.get("source_matches")})
    report["integration_evidence"]["plugin_link_state"] = "linked_now"
    poll_runtime_tools(openclaw_bin, cwd, plugin_root, report, "post_link_readiness")


def validate_config(openclaw_bin: str, cwd: Path, report: dict[str, Any]) -> None:
    report["config_validation"]["attempted"] = True
    run_checked([openclaw_bin, "config", "validate"], cwd=cwd, code="config_validate_failed", timeout=CONFIG_TIMEOUT_SECONDS)
    report["config_validation"].update({"ok": True})


def restart_gateway(openclaw_bin: str, cwd: Path, report: dict[str, Any]) -> None:
    report["gateway_restart_or_reload"]["attempted"] = True
    result = run_capture([openclaw_bin, "gateway", "restart"], cwd=cwd, check=False, timeout=60)
    report["gateway_restart_or_reload"].update(
        {"ok": result.returncode == 0, "returncode": result.returncode, "message": safe_message(result.stdout or result.stderr)}
    )
    if result.returncode != 0:
        report["errors"].append({"code": "gateway_restart_failed", "message": safe_message(result.stdout or result.stderr)})


def gateway_status(openclaw_bin: str, cwd: Path, report: dict[str, Any]) -> None:
    report["gateway_status"]["attempted"] = True
    result = run_capture(
        [openclaw_bin, "gateway", "status", "--deep", "--require-rpc", "--json"],
        cwd=cwd,
        check=False,
        timeout=60,
    )
    report["gateway_status"].update({"ok": result.returncode == 0, "returncode": result.returncode})
    if result.stdout.strip().startswith("{"):
        report["gateway_status"]["details"] = redact(json.loads(result.stdout))
    else:
        report["gateway_status"]["message"] = safe_message(result.stdout or result.stderr)
    if result.returncode != 0:
        report["errors"].append({"code": "gateway_status_failed", "message": safe_message(result.stdout or result.stderr)})


def inspect_runtime(openclaw_bin: str, cwd: Path, report: dict[str, Any]) -> None:
    report["runtime_inspection"]["attempted"] = True
    result = run_capture(
        [openclaw_bin, "plugins", "inspect", PLUGIN_ID, "--runtime", "--json"],
        cwd=cwd,
        check=False,
        timeout=INSPECT_TIMEOUT_SECONDS,
    )
    report["runtime_inspection"].update({"ok": result.returncode == 0, "returncode": result.returncode})
    if result.returncode != 0:
        report["runtime_inspection"]["message"] = safe_message(result.stdout or result.stderr)
        report["errors"].append({"code": "runtime_inspection_failed", "message": safe_message(result.stdout or result.stderr)})
        return
    details = json.loads(result.stdout)
    report["runtime_inspection"]["details"] = redact(details)
    tools = details.get("plugin", {}).get("toolNames", [])
    report["read_tools_visible"] = [tool for tool in READ_TOOLS if tool in tools]
    report["write_candidate_visible"] = any(
        WRITE_TOOL in item.get("names", []) and item.get("optional") is False for item in details.get("tools", [])
    )
    report["integration_evidence"]["runtime_tool_names"] = list(tools)
    report["integration_evidence"]["required_read_tools_visible"] = all(tool in tools for tool in READ_TOOLS)
    report["integration_evidence"]["write_candidate_default_enabled"] = bool(report["write_candidate_visible"])


def run_sidecar_probe(repo_root: Path, workspace_root: Path, probe_query: str, report: dict[str, Any]) -> None:
    out_dir = workspace_root / ".nollm-memory"
    script = repo_root / "reference/python/scripts/run_openclaw_nollm_memory.py"
    report["sidecar_probe"]["attempted"] = True
    index = run_capture(
        ["python", str(script), "--repo-root", str(repo_root), "index", "--workspace", str(workspace_root), "--out", str(out_dir)],
        cwd=repo_root / "reference/python",
        check=False,
        timeout=60,
    )
    status = run_capture(
        ["python", str(script), "--repo-root", str(repo_root), "status", "--workspace", str(workspace_root), "--out", str(out_dir)],
        cwd=repo_root / "reference/python",
        check=False,
        timeout=60,
    )
    search = run_capture(
        [
            "python",
            str(script),
            "--repo-root",
            str(repo_root),
            "search",
            "--workspace",
            str(workspace_root),
            "--out",
            str(out_dir),
            "--query",
            probe_query,
            "--limit",
            "3",
        ],
        cwd=repo_root / "reference/python",
        check=False,
        timeout=60,
    )
    report["sidecar_probe"].update(
        {
            "ok": index.returncode == 0 and status.returncode == 0 and search.returncode == 0,
            "index_returncode": index.returncode,
            "status_returncode": status.returncode,
            "search_returncode": search.returncode,
            "manual_chat_prompt": "Use Nollm memory search to find what this workspace remembers about <topic>. Show the source and explain the drift class before relying on it.",
        }
    )
    if report["sidecar_probe"]["ok"]:
        status_report = json.loads(status.stdout)
        search_report = json.loads(search.stdout)
        report["sidecar_probe"]["status"] = redact(status_report)
        report["sidecar_probe"]["search"] = summarize_search(search_report)
        report["integration_evidence"]["sidecar_index_ok"] = index.returncode == 0
        report["integration_evidence"]["sidecar_search_ok"] = search.returncode == 0
        report["integration_evidence"]["sidecar_result_count"] = int(search_report.get("result_count") or 0)
    else:
        report["errors"].append({"code": "sidecar_probe_failed", "message": safe_message(index.stderr + status.stderr + search.stderr)})


def check_skill_manifest(plugin_root: Path) -> dict[str, Any]:
    manifest = read_json_file(plugin_root / "openclaw.plugin.json")
    skill_path = plugin_root / "skill/SKILL.md"
    return {
        "attempted": True,
        "ok": manifest.get("skills") == ["skill"] and skill_path.exists(),
        "manifest_skills": manifest.get("skills"),
    }


def inspect_installed_plugin_state(openclaw_bin: str, cwd: Path, plugin_root: Path) -> dict[str, Any]:
    result = run_capture(
        [openclaw_bin, "plugins", "inspect", PLUGIN_ID, "--runtime", "--json"],
        cwd=cwd,
        check=False,
        timeout=INSPECT_TIMEOUT_SECONDS,
    )
    if result.returncode != 0 or not result.stdout.strip().startswith("{"):
        return {"present": False, "source_matches": False, "enabled": False, "returncode": result.returncode}
    details = json.loads(result.stdout)
    plugin = details.get("plugin", {})
    install = details.get("install", {})
    candidates = [
        plugin.get("rootDir"),
        install.get("installPath"),
        install.get("sourcePath"),
        details.get("sourcePath"),
    ]
    canonical_root = canonical_path(plugin_root)
    source_matches = any(canonical_path(Path(candidate)) == canonical_root for candidate in candidates if isinstance(candidate, str))
    return {
        "present": True,
        "source_matches": source_matches,
        "enabled": plugin.get("enabled") is True,
        "status": plugin.get("status"),
    }


def poll_runtime_tools(openclaw_bin: str, cwd: Path, plugin_root: Path, report: dict[str, Any], field: str) -> None:
    deadline = time.monotonic() + READINESS_DEADLINE_SECONDS
    attempts = 0
    last_state: dict[str, Any] = {}
    report[field] = {
        "attempted": True,
        "ok": False,
        "deadline_seconds": READINESS_DEADLINE_SECONDS,
        "poll_interval_seconds": READINESS_POLL_INTERVAL_SECONDS,
    }
    while time.monotonic() <= deadline:
        attempts += 1
        last_state = inspect_installed_plugin_state(openclaw_bin, cwd, plugin_root)
        if last_state.get("source_matches") is True and last_state.get("enabled") is True:
            report[field].update({"ok": True, "attempts": attempts, "final_state": last_state})
            return
        time.sleep(READINESS_POLL_INTERVAL_SECONDS)
    report[field].update(
        {
            "ok": False,
            "attempts": attempts,
            "final_state": last_state,
            "timeout_reason": "plugin readiness was not reached before deadline",
        }
    )
    report["errors"].append({"code": f"{field}_timeout", "message": "OpenClaw plugin readiness was not reached before deadline."})


def discover_workspace(openclaw_bin: str, cwd: Path) -> Path:
    result = run_capture([openclaw_bin, "config", "get", "agents.defaults.workspace", "--json"], cwd=cwd, check=False)
    if result.returncode == 0 and result.stdout.strip():
        value = json.loads(result.stdout)
        if isinstance(value, str) and value:
            return Path(value).expanduser().resolve()
    config_path = Path(run_capture([openclaw_bin, "config", "file"], cwd=cwd).stdout.strip()).resolve()
    return (config_path.parent / "workspace").resolve()


def hash_source_memory_files(workspace_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in source_memory_files(workspace_root):
        relative = path.relative_to(workspace_root).as_posix()
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(sorted(hashes.items()))


def source_memory_files(workspace_root: Path) -> list[Path]:
    files: list[Path] = []
    for name in ["MEMORY.md", "DREAMS.md"]:
        path = workspace_root / name
        if path.exists() and path.is_file():
            files.append(path)
    memory_dir = workspace_root / "memory"
    if memory_dir.exists():
        files.extend(path for path in sorted(memory_dir.glob("**/*.md")) if path.is_file())
    return files


def finish_source_hash_evidence(workspace_root: Path, report: dict[str, Any]) -> None:
    after = hash_source_memory_files(workspace_root)
    evidence = report["integration_evidence"]
    evidence["source_memory_hashes_after"] = after
    evidence["source_memory_unchanged"] = evidence.get("source_memory_hashes_before") == after


def canonical_path(path: Path) -> Path:
    try:
        return Path(os.path.realpath(path)).resolve()
    except OSError:
        return path.resolve()


def git_repo_root() -> Path:
    return Path(run_capture(["git", "rev-parse", "--show-toplevel"], cwd=Path.cwd()).stdout.strip()).resolve()


def write_report(report: dict[str, Any], args: argparse.Namespace) -> None:
    path = Path(args.report_path).resolve() if args.report_path else None
    if path is None:
        workspace = report.get("workspace_root")
        base = Path(workspace) if workspace else Path.cwd()
        path = base / ".nollm-memory/integration/openclaw_integration_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    report["report_path"] = str(path)
    path.write_text(json.dumps(redact(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_checked(command: list[str], *, cwd: Path, code: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    result = run_capture(command, cwd=cwd, check=False, timeout=timeout)
    if result.returncode != 0:
        raise InstallerError(code, safe_message(result.stdout or result.stderr))
    return result


def run_capture(command: list[str], *, cwd: Path, check: bool = True, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    if check and result.returncode != 0:
        raise InstallerError("command_failed", safe_message(result.stdout or result.stderr))
    return result


def read_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_nested(data: dict[str, Any], path_items: list[str]) -> Any:
    current: Any = data
    for item in path_items:
        if not isinstance(current, dict) or item not in current:
            return None
        current = current[item]
    return current


def union_preserve(existing: list[str], additions: list[str]) -> list[str]:
    result = list(existing)
    for item in additions:
        if item not in result:
            result.append(item)
    return result


def summarize_patch(patch: dict[str, Any]) -> dict[str, Any]:
    plugin_entry = patch["plugins"]["entries"][PLUGIN_ID]
    return {
        "plugin_enabled": plugin_entry["enabled"],
        "config_fields": sorted(plugin_entry["config"]),
        "tools_allow_updated": "tools" in patch and "allow" in patch["tools"],
        "write_candidate_requested": WRITE_TOOL in patch.get("tools", {}).get("allow", []),
    }


def summarize_search(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": report.get("ok"),
        "result_count": report.get("result_count"),
        "first_result_keys": sorted(report.get("results", [{}])[0].keys()) if report.get("results") else [],
    }


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            lower = key.lower()
            if any(secret in lower for secret in ["token", "secret", "password", "apikey", "api_key"]):
                redacted[key] = "<redacted>"
            else:
                redacted[key] = redact(item)
        return redacted
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def safe_message(message: str) -> str:
    return " ".join(message.split())[:500]


class InstallerError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


if __name__ == "__main__":
    raise SystemExit(main())
