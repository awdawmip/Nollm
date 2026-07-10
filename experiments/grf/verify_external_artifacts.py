from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys


MANIFEST_NAME = "GRF7R_EXTERNAL_ARTIFACT_MANIFEST.json"


def build_manifest(root: Path, generation_command: str) -> dict[str, object]:
    root = Path(root).resolve()
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and item.name != MANIFEST_NAME):
        digest = sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        files.append({"relative_path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": digest.hexdigest()})
    if not files:
        raise ValueError("external artifact root contains no files")
    merkle_payload = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"schema": "grf7r_external_artifacts_v1", "file_count": len(files), "files": files, "merkle_root_sha256": sha256(merkle_payload).hexdigest(), "generation_command": generation_command}


def verify(root: Path) -> tuple[bool, str]:
    root = Path(root).resolve()
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.is_file():
        return False, "UNVERIFIED: external artifact manifest is missing"
    try:
        expected = json.loads(manifest_path.read_text(encoding="utf-8"))
        actual = build_manifest(root, str(expected["generation_command"]))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return False, f"UNVERIFIED: {exc}"
    if expected != actual:
        return False, "UNVERIFIED: external artifact bytes, inventory, or Merkle root changed"
    return True, f"VERIFIED: {actual['file_count']} files, Merkle root {actual['merkle_root_sha256']}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(os.environ.get("NOLLM_GRF7R_EXTERNAL_ROOT", r"C:\Users\chaos\nollm_grf7_external_evidence_20260710")))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--generation-command", default="python experiments/grf/run_grf7r_real_global_workload.py && python experiments/grf/run_grf7r_runtime_semantics.py && python experiments/grf/run_grf7r_long_running_validation.py && python experiments/grf/run_grf7r_workflow_validation.py")
    args = parser.parse_args()
    if args.write:
        manifest = build_manifest(args.root, args.generation_command)
        (args.root / MANIFEST_NAME).write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    passed, message = verify(args.root)
    print(message)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
