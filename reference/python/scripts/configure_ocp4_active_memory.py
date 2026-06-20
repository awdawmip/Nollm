from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.openclaw_active_memory_config import OCP4_AGENT_ID, build_ocp4_active_memory_patch  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Configure the controlled OCP4 Nollm Active Memory agent.")
    parser.add_argument("--openclaw-bin", default=None)
    parser.add_argument("--repo-root", default="../..")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--agent-id", default=OCP4_AGENT_ID)
    parser.add_argument("--model", default="kimi/kimi-for-coding")
    parser.add_argument("--transcript-dir", default=None)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--patch-out", default=None)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    workspace = Path(args.workspace).resolve()
    openclaw_bin = args.openclaw_bin or shutil.which("openclaw")
    if not openclaw_bin:
        raise SystemExit("openclaw executable was not found")
    config_path = Path(
        subprocess.run([openclaw_bin, "config", "file"], cwd=repo_root, text=True, capture_output=True, check=True).stdout.strip()
    ).expanduser()
    config_before = json.loads(config_path.read_text(encoding="utf-8"))
    patch = build_ocp4_active_memory_patch(
        config_before=config_before,
        repo_root=repo_root,
        workspace_root=workspace,
        agent_id=args.agent_id,
        model=args.model,
        transcript_dir=args.transcript_dir,
    )
    if args.patch_out:
        Path(args.patch_out).write_text(json.dumps(patch, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.apply:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            json.dump(patch, handle, indent=2, sort_keys=True)
            patch_path = Path(handle.name)
        try:
            subprocess.run(
                [openclaw_bin, "config", "patch", "--file", str(patch_path), "--replace-path", "agents.list"],
                cwd=repo_root,
                text=True,
                check=True,
            )
            subprocess.run([openclaw_bin, "config", "validate"], cwd=repo_root, text=True, check=True)
        finally:
            patch_path.unlink(missing_ok=True)
    print(json.dumps({"ok": True, "agent_id": args.agent_id, "apply": bool(args.apply), "patch": patch}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
