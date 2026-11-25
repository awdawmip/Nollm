"""Build an independent native field deployment in an explicit new directory.

The deployment contains a portable runtime, a field copy and fixed source files.
It does not install a personal skill, change account instructions or connect the
field to another knowledge system's default entry.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from shutil import copytree
from tempfile import TemporaryDirectory

from install_skill import install
from source_snapshot import SourceSnapshot


LAUNCHER = '''"""Open this independent Nollm deployment."""
import argparse
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, default=ROOT / "field",
                        help="native field; put this option before the command")
    parser.add_argument("command", choices=("encounter", "walk", "show", "source", "save",
                                            "storage", "links", "stitch", "unstitch", "find", "local-p8"))
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    memory = ROOT / "runtime/scripts/memory.py"
    if args.command == "local-p8":
        arguments = ["aux", "local-p8", *args.arguments]
    else:
        arguments = ["project", "--field", str(args.field), args.command, *args.arguments]
        providers = {value.partition("=")[0] for value in args.arguments}
        if args.command in {"source", "save", "encounter"} and not providers & {"--repo", "--snapshot"}:
            arguments.extend(["--snapshot", str(ROOT / "snapshot")])
    sys.argv = [str(memory), *arguments]
    runpy.run_path(str(memory), run_name="__main__")

if __name__ == "__main__":
    main()
'''


def build(destination, *, field, snapshot, runtime_commit):
    """Copy a settled field and available evidence; report partial source copies."""
    destination = Path(destination).expanduser().absolute()
    field, snapshot = Path(field).resolve(), Path(snapshot).resolve()
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"destination already exists: {destination}; choose a new directory")
    destination = destination.resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", runtime_commit):
        raise ValueError("runtime_commit must be a full Git commit SHA")
    if not (field / "core/current_state.json").is_file():
        raise ValueError(f"field has no persisted Core state: {field}")
    if (field / "access/reorganization.pending.json").exists():
        raise ValueError("field has pending reorganization; reopen and complete recovery before deployment")
    for source in (field, snapshot):
        if destination.is_relative_to(source):
            raise ValueError("deployment destination must be outside its source field and snapshot")
    source = SourceSnapshot(snapshot)
    source_files = snapshot / "files"
    materialized = {str(path.relative_to(source_files).as_posix())
                    for path in source_files.rglob("*") if path.is_file()}
    undeclared = materialized - source.files.keys()
    if undeclared:
        raise ValueError(f"snapshot contains undeclared files: {sorted(undeclared)[:3]}")
    metadata = {
        "schema": "nollm_independent_deployment_v1",
        "runtime_repository": "awdawmip/Nollm", "runtime_commit": runtime_commit,
        "source_repository": source.repository, "source_commit": source.commit,
        "field": "field", "snapshot": "snapshot", "launcher": "run.py",
        "source_materialization": {
            "declared_files": len(source.files), "materialized_files": len(materialized),
            "complete": len(materialized) == len(source.files),
        },
        "field_geometry": "Core Q40/96; existing field profile",
        "local_p8": "explicit Lab evaluation only; run.py local-p8",
        "automatic_entry_integration": False,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent, prefix=".nollm-deploy-") as temporary:
        root = Path(temporary) / "deployment"
        root.mkdir()
        install(root / "runtime")
        copytree(field, root / "field")
        copytree(snapshot, root / "snapshot")
        (root / "run.py").write_text(LAUNCHER, encoding="utf-8")
        (root / "deployment.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8")
        root.rename(destination)
    return metadata


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--runtime-commit", required=True)
    args = parser.parse_args(argv)
    try:
        result = build(args.dest, field=args.field, snapshot=args.snapshot, runtime_commit=args.runtime_commit)
    except (OSError, TypeError, ValueError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
