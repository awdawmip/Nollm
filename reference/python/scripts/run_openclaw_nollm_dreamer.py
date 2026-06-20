from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Mapping

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.dream_cortex_recall import DREAMER_CONTRACT_SCHEMA, publish_dreamer_delta, source_snapshot  # noqa: E402


FORBIDDEN_PROMPT_TERMS = ("user question", "query:", "answer:", "top_k", "rank", "q/r/layer")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh a Nollm dream field through a bounded OpenClaw Dreamer agent.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    refresh_parser = subparsers.add_parser("refresh")
    refresh_parser.add_argument("--workspace", required=True)
    refresh_parser.add_argument("--out", required=True)
    refresh_parser.add_argument("--openclaw-bin", default="openclaw")
    refresh_parser.add_argument("--agent", default="nollm-dreamer")
    refresh_parser.add_argument("--field-id", default="openclaw-dream-field")
    refresh_parser.add_argument("--timeout-seconds", type=int, default=120)
    refresh_parser.add_argument("--mock-dreamer-output", default=None)
    refresh_parser.add_argument("--force", action="store_true", help="Call the Dreamer even when the source snapshot is unchanged.")

    args = parser.parse_args(argv)
    if args.command == "refresh":
        report = refresh_field(args)
    else:
        raise AssertionError("unreachable command")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report.get("ok") is True else 1


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

    prompt = build_dreamer_prompt(snapshot, current, field_id=args.field_id)
    if args.mock_dreamer_output:
        raw = Path(args.mock_dreamer_output).resolve().read_text(encoding="utf-8")
        run_ref = {"kind": "mock_openclaw_dreamer", "path": str(Path(args.mock_dreamer_output).resolve())}
    else:
        live = _run_openclaw_agent(args.openclaw_bin, args.agent, prompt, int(args.timeout_seconds))
        if live["ok"] is False:
            return {
                "ok": False,
                "status": "live_dreamer_blocked",
                "source_snapshot_hash": snapshot["source_snapshot_hash"],
                "dreamer_called": True,
                "error": live["error"],
                "diagnostics": live.get("diagnostics", {}),
            }
        raw = str(live["stdout"])
        run_ref = {"kind": "live_openclaw_agent", "agent": args.agent, "openclaw_bin": args.openclaw_bin}

    try:
        delta = _parse_single_json_object(raw)
        published = publish_dreamer_delta(workspace, out_dir, delta, dreamer_run_ref=run_ref)
    except Exception as exc:
        return {
            "ok": False,
            "status": "invalid_dreamer_output",
            "source_snapshot_hash": snapshot["source_snapshot_hash"],
            "dreamer_called": True,
            "error": str(exc),
        }
    published["dreamer_called"] = True
    return published


def build_dreamer_prompt(snapshot: Mapping[str, object], current_field: Mapping[str, object] | None, *, field_id: str) -> str:
    source_files = []
    for item in snapshot.get("source_files", []):
        if isinstance(item, Mapping):
            source_files.append(
                {
                    "source_path": item.get("source_path"),
                    "sha256": item.get("sha256"),
                    "byte_count": item.get("byte_count"),
                    "line_count": item.get("line_count"),
                }
            )
    prior = []
    for shard in (current_field or {}).get("shards", []):
        if isinstance(shard, Mapping):
            prior.append({"semantic_key": shard.get("semantic_key"), "scale": shard.get("scale"), "status": shard.get("status")})
        if len(prior) >= 20:
            break
    contract = {
        "schema": DREAMER_CONTRACT_SCHEMA,
        "source_snapshot_hash": snapshot["source_snapshot_hash"],
        "field_id": field_id,
        "allowed_shard_fields": [
            "semantic_key",
            "text",
            "status",
            "preferred_scale",
            "anchors",
            "source_links",
            "continuity",
            "near_intents",
            "bridge_intents",
        ],
        "forbidden_fields": ["q", "r", "layer", "HexAddress", "rank", "score", "query", "answer", "top_k", "embedding"],
        "source_files": source_files,
        "prior_field_summary": prior,
    }
    return (
        "You are the Nollm Dreamer. Emit exactly one JSON object and no prose.\n"
        "Dream independent semantic shards from the read-only source snapshot metadata. "
        "Do not answer a user, do not rank, and do not invent coordinates. "
        "Every source_link must reference a listed source_path, sha256, and valid line_range.\n"
        + json.dumps(contract, ensure_ascii=False, sort_keys=True)
    )


def _run_openclaw_agent(openclaw_bin: str, agent: str, prompt: str, timeout_seconds: int) -> dict[str, object]:
    try:
        completed = subprocess.run(
            [openclaw_bin, "agent", "--agent", agent, "--message", prompt, "--json"],
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
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


def _parse_single_json_object(raw: str) -> dict[str, object]:
    text = raw.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Dreamer output did not contain a JSON object")
        data = json.loads(text[start : end + 1])
        trailing = text[end + 1 :].strip()
        leading = text[:start].strip()
        if leading or trailing:
            raise ValueError("Dreamer output must contain exactly one JSON object")
    if not isinstance(data, dict):
        raise ValueError("Dreamer output must be a JSON object")
    return data


def _load_current_field(out_dir: Path) -> dict[str, object] | None:
    pointer = out_dir / "current_field.json"
    if not pointer.exists():
        return None
    current = json.loads(pointer.read_text(encoding="utf-8"))
    return json.loads((out_dir / str(current["path"]) / "dream_field.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
