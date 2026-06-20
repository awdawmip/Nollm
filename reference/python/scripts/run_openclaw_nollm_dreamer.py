from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_cortex_recall import (  # noqa: E402
    DREAMER_CONTRACT_SCHEMA,
    build_dream_packet,
    publish_dreamer_delta,
    source_snapshot,
)
from nollm.openclaw_active_memory_config import (  # noqa: E402
    DIRECT_TOOL_DENY,
    OCP7_DREAMER_AGENT_ID,
)


DREAMER_DENY_TOOLS = DIRECT_TOOL_DENY + [
    "memory_search",
    "memory_get",
    "nollm_memory_search",
    "nollm_memory_get",
    "nollm_memory_recall",
    "nollm_field_overview",
    "nollm_open_well",
    "nollm_surface",
    "nollm_focus",
    "nollm_drift",
    "nollm_read",
    "nollm_recall_trace",
]
PROMPT_FORBIDDEN_TERMS = ("memory_search", "memory_get", "nollm_memory_search", "nollm_memory_get", "web_search", "web_fetch")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Configure and run a bounded OpenClaw Nollm Dreamer agent.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    configure = subparsers.add_parser("configure")
    configure.add_argument("--openclaw-bin", default="openclaw")
    configure.add_argument("--workspace", required=True)
    configure.add_argument("--config-path", default=None)
    configure.add_argument("--agent", default=OCP7_DREAMER_AGENT_ID)
    configure.add_argument("--model", default=None)
    configure.add_argument("--apply", action="store_true")
    configure.add_argument("--dry-run", action="store_true")

    refresh_parser = subparsers.add_parser("refresh")
    refresh_parser.add_argument("--workspace", required=True)
    refresh_parser.add_argument("--out", required=True)
    refresh_parser.add_argument("--openclaw-bin", default="openclaw")
    refresh_parser.add_argument("--agent", default=OCP7_DREAMER_AGENT_ID)
    refresh_parser.add_argument("--field-id", default="openclaw-dream-field")
    refresh_parser.add_argument("--timeout-seconds", type=int, default=120)
    refresh_parser.add_argument("--mock-dreamer-output", default=None)
    refresh_parser.add_argument("--force", action="store_true", help="Call the Dreamer even when the source snapshot is unchanged.")
    refresh_parser.add_argument("--packet-out", default=None)

    args = parser.parse_args(argv)
    if args.command == "configure":
        report = configure_dreamer(args)
    elif args.command == "refresh":
        report = refresh_field(args)
    else:
        raise AssertionError("unreachable command")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report.get("ok") is True else 1


def configure_dreamer(args: argparse.Namespace) -> dict[str, object]:
    dry_run = bool(args.dry_run or not args.apply)
    openclaw = str(args.openclaw_bin)
    workspace = str(Path(args.workspace).resolve())
    config_path = Path(args.config_path).resolve() if args.config_path else Path(_run_json_or_text([openclaw, "config", "file"]).strip()).resolve()
    schema = _run_json_or_text([openclaw, "config", "schema"])
    agents_before = _run_json([openclaw, "agents", "list", "--json"])
    config_before = json.loads(config_path.read_text(encoding="utf-8"))
    model = args.model or _derive_model(agents_before, config_before)
    patch = _build_agent_patch(config_before, agent_id=args.agent, workspace=workspace, model=model)
    patch_result = _apply_patch(openclaw, patch, dry_run=dry_run)
    validate = _run_json_or_text([openclaw, "config", "validate"]) if not dry_run else "dry_run_not_applied"
    agents_after = _run_json([openclaw, "agents", "list", "--json"]) if not dry_run else agents_before
    visible = any(isinstance(item, Mapping) and item.get("id") == args.agent for item in agents_after)
    return {
        "ok": dry_run or visible,
        "status": "dry_run" if dry_run else "configured",
        "agent": args.agent,
        "model": model,
        "config_path": str(config_path),
        "schema_observed": bool(schema),
        "patch_result": _redact(patch_result),
        "validate": validate.strip()[:500] if isinstance(validate, str) else validate,
        "agent_visible": visible,
        "context_injection": "never",
        "allowed_tool_count": 0,
    }


def refresh_field(args: argparse.Namespace) -> dict[str, object]:
    workspace = Path(args.workspace).resolve()
    out_dir = Path(args.out).resolve()
    snapshot = source_snapshot(workspace)
    current = _load_current_field(out_dir)
    if not args.force and current and current.get("source_snapshot_hash") == snapshot["source_snapshot_hash"]:
        return {
            "ok": True,
            "status": "no_change",
            "field_id": current.get("field_id"),
            "revision_id": current.get("revision_id"),
            "source_snapshot_hash": snapshot["source_snapshot_hash"],
            "dreamer_called": False,
        }

    packet = build_dream_packet(workspace, field_id=args.field_id, current_field=current)
    if args.packet_out:
        packet_path = Path(args.packet_out).resolve()
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        packet_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    prompt = build_dreamer_prompt(packet)
    if args.mock_dreamer_output:
        raw = Path(args.mock_dreamer_output).resolve().read_text(encoding="utf-8")
        run_ref = {"kind": "mock_openclaw_dreamer", "path": str(Path(args.mock_dreamer_output).resolve())}
    else:
        live = _run_openclaw_agent(args.openclaw_bin, args.agent, prompt, int(args.timeout_seconds))
        if live["ok"] is False:
            return {
                "ok": False,
                "status": "live_dreamer_blocked",
                "block_category": _classify_live_block(str(live["error"])),
                "source_snapshot_hash": snapshot["source_snapshot_hash"],
                "dreamer_called": True,
                "error": live["error"],
                "diagnostics": live.get("diagnostics", {}),
            }
        try:
            raw = _extract_agent_text(str(live["stdout"]))
        except Exception as exc:
            return {
                "ok": False,
                "status": "invalid_dreamer_output",
                "block_category": "invalid_live_output",
                "source_snapshot_hash": snapshot["source_snapshot_hash"],
                "dreamer_called": True,
                "error": str(exc),
            }
        run_ref = {"kind": "live_openclaw_agent", "agent": args.agent, "openclaw_bin": args.openclaw_bin}

    try:
        delta = _parse_single_json_object(raw)
        published = publish_dreamer_delta(workspace, out_dir, delta, dreamer_run_ref=run_ref, dream_packet=packet)
    except Exception as exc:
        return {
            "ok": False,
            "status": "invalid_dreamer_output",
            "source_snapshot_hash": snapshot["source_snapshot_hash"],
            "dreamer_called": True,
            "error": str(exc),
        }
    published["dreamer_called"] = True
    published["dream_packet_material_count"] = len(packet["source_material"]) if isinstance(packet.get("source_material"), list) else 0
    return published


def build_dreamer_prompt(packet: Mapping[str, object]) -> str:
    contract = {
        "task": "Distill the provided read-only Dream Packet into semantic dream shards.",
        "output_schema": DREAMER_CONTRACT_SCHEMA,
        "packet": packet,
        "allowed_status": ["source_backed", "derived", "tentative"],
        "allowed_preferred_scale": ["coarse", "bridge", "fine"],
        "forbidden_fields": ["q", "r", "layer", "HexAddress", "rank", "score", "query", "answer", "top_k", "embedding"],
        "requirements": [
            "Emit exactly one JSON object and no prose.",
            "Top-level keys must be exactly schema, source_snapshot_hash, field_id, shards, and cluster_intents.",
            "Each shard must use semantic_key and text; do not use shard_id or intent.",
            "Use source_links that point only into packet source_material.",
            "Each source_link must include source_path, source_sha256, and line_range; do not use material_id as a substitute.",
            "Include Chinese and English source-backed shards when present.",
            "Do not write files, call tools, rank search hits, answer a user, or invent geometry coordinates.",
        ],
        "minimal_shape": {
            "schema": DREAMER_CONTRACT_SCHEMA,
            "source_snapshot_hash": packet.get("source_snapshot_hash"),
            "field_id": packet.get("field_id"),
            "shards": [
                {
                    "semantic_key": "stable-lowercase-key",
                    "text": "one independently meaningful dream sentence",
                    "status": "source_backed",
                    "preferred_scale": "coarse",
                    "anchors": ["anchor"],
                    "source_links": [{"source_path": "MEMORY.md", "source_sha256": "<copy from packet source_material>", "line_range": [1, 1]}],
                    "continuity": {"prior_semantic_key": None},
                    "near_intents": [],
                    "bridge_intents": [],
                }
            ],
            "cluster_intents": [{"label": "cluster label", "members": ["stable-lowercase-key"]}],
        },
    }
    prompt = (
        "You are the Nollm Dreamer. You receive a Dream Packet containing actual read-only MEMORY.md text. "
        "Create source-bound semantic intent for Nollm Core placement. "
        "The current user message is unavailable and must not be inferred. DREAM_PACKET_JSON="
        + json.dumps(contract, ensure_ascii=False, sort_keys=True)
    )
    lowered = prompt.lower()
    for term in PROMPT_FORBIDDEN_TERMS:
        if term in lowered:
            raise ValueError(f"forbidden tool name leaked into Dreamer prompt: {term}")
    return prompt


def _build_agent_patch(config_before: Mapping[str, Any], *, agent_id: str, workspace: str, model: str) -> dict[str, object]:
    agents = list(((config_before.get("agents") or {}) if isinstance(config_before.get("agents"), Mapping) else {}).get("list") or [])
    agents = [item for item in agents if isinstance(item, Mapping) and item.get("id") != agent_id]
    agents.append(
        {
            "id": agent_id,
            "name": agent_id,
            "workspace": workspace,
            "agentDir": str(Path.home() / ".openclaw" / "agents" / agent_id / "agent"),
            "model": model,
            "contextInjection": "never",
            "bootstrapMaxChars": 1,
            "bootstrapTotalMaxChars": 1,
            "memorySearch": {"provider": "none", "fallback": "none"},
            "tools": {"profile": "minimal", "alsoAllow": [], "deny": DREAMER_DENY_TOOLS},
        }
    )
    return {"agents": {"list": agents}}


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
        command = [openclaw, "config", "patch", "--file", str(patch_path)]
        if dry_run:
            command.extend(["--dry-run", "--json"])
        output = _run_json_or_text(command)
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {"stdout": output.strip()[:1000]}
    finally:
        patch_path.unlink(missing_ok=True)


def _run_openclaw_agent(openclaw_bin: str, agent: str, prompt: str, timeout_seconds: int) -> dict[str, object]:
    try:
        completed = subprocess.run(
            _command_prefix(openclaw_bin)
            + [
                "agent",
                "--agent",
                agent,
                "--session-key",
                f"agent:{agent}:dreamer-{_sha256_text(prompt)[:12]}",
                "--message",
                prompt,
                "--json",
                "--timeout",
                str(timeout_seconds),
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout_seconds + 30,
            check=False,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc), "diagnostics": {"exception_type": type(exc).__name__}}
    if completed.returncode != 0:
        return {
            "ok": False,
            "error": (completed.stderr or completed.stdout or "OpenClaw Dreamer agent failed.").strip()[:2000],
            "diagnostics": {"returncode": completed.returncode},
        }
    return {"ok": True, "stdout": completed.stdout}


def _extract_agent_text(stdout: str) -> str:
    data = json.loads(stdout)
    candidates: list[object] = []
    if isinstance(data, Mapping):
        for key in ("text", "message", "content", "response", "reply", "output"):
            if key in data:
                candidates.append(data[key])
        result = data.get("result")
        if isinstance(result, Mapping):
            for key in ("text", "message", "content", "response", "reply", "output"):
                if key in result:
                    candidates.append(result[key])
            payloads = result.get("payloads")
            if isinstance(payloads, list):
                for payload in payloads:
                    if isinstance(payload, Mapping) and isinstance(payload.get("text"), str):
                        candidates.append(payload["text"])
    strings = [item for item in candidates if isinstance(item, str) and item.strip()]
    if len(strings) != 1:
        raise ValueError("OpenClaw agent JSON envelope did not contain exactly one textual response")
    return _strip_json_fence(strings[0])


def _parse_single_json_object(raw: str) -> dict[str, object]:
    text = raw.strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Dreamer output must be a JSON object")
    return data


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 3 and lines[0].strip().lower() in {"```json", "```"} and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    raise ValueError("Dreamer output used an unsupported code fence")


def _classify_live_block(error: str) -> str:
    lowered = error.lower()
    if "unknown agent" in lowered:
        return "agent_missing"
    if "auth" in lowered or "api key" in lowered or "unauthorized" in lowered:
        return "auth_unavailable"
    if "model" in lowered:
        return "model_unavailable"
    if "gateway" in lowered or "connect" in lowered or "econn" in lowered:
        return "gateway_unreachable"
    if "json" in lowered or "schema" in lowered:
        return "invalid_live_output"
    return "provider_failure"


def _run_json(command: list[str]) -> object:
    return json.loads(_run_json_or_text(command))


def _run_json_or_text(command: list[str]) -> str:
    completed = subprocess.run(command, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=60)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "OpenClaw command failed").strip())
    return completed.stdout


def _command_prefix(executable: str) -> list[str]:
    if sys.platform.startswith("win") and executable.lower().endswith((".cmd", ".ps1")):
        base = Path(executable).resolve().parent
        node = base / "node.exe"
        mjs = base / "node_modules" / "openclaw" / "openclaw.mjs"
        if node.exists() and mjs.exists():
            return [str(node), str(mjs)]
        return ["cmd.exe", "/d", "/c", executable]
    return [executable]


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


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_current_field(out_dir: Path) -> dict[str, object] | None:
    pointer = out_dir / "current_field.json"
    if not pointer.exists():
        return None
    current = json.loads(pointer.read_text(encoding="utf-8"))
    return json.loads((out_dir / str(current["path"]) / "dream_field.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
