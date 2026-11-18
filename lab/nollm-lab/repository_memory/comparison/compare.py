"""Prepare fresh three-arm change trials and score candidate patches."""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import tarfile

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
BASE = "314eb47490adcad22e37d6e05d2da3983e78956d"
TASKS = {
    "digest": "Expose CoreRuntime.state_sha256() as a lowercase hex SHA-256 of the exact canonical exported state. Route AccessRuntime.apply_if_state through that public method under its existing operation guard, preserving stale zero-write and success results. Keep the persisted format and snapshot API compatible.",
    "binding": "Add FileHandleStore.statement_ids_for_handle(handle) and AccessRuntime.statement_ids_for_handle(handle). Return a tuple with the current statement ID first, followed by canonical supporting IDs, preserve KeyError for an unknown handle, and honor AccessRuntime's operation lifecycle. Leave persisted bytes and ordinary recall intact.",
    "statement": "Add MemoryStatement.canonical_bytes() and FileStatementStore.canonical_bytes(statement_id) for exporting the canonical UTF-8 bytes of the statement mapping alone. Use sorted keys, compact separators, literal Unicode and a trailing LF. Store export must validate existing records including legacy evidence through normal reads, preserving missing/corrupt errors and on-disk format.",
}
ARMS = ("direct", "overview", "field", "field-view")


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, **kwargs).stdout


def packet(repo, task, arm, manifest=None):
    prompt = TASKS[task] + "\n"
    manifest = manifest or LAB / "examples" / "nollm-notes.json"
    if arm == "field-repaired":
        # A reviewed observation written after the original digest failure.
        with TemporaryDirectory() as directory:
            enriched = Path(directory) / "notes.json"
            shutil.copyfile(manifest, enriched)
            run([sys.executable, LAB / "repo_notes.py", "capture", "--repo", repo,
                 "--rev", BASE, "--manifest", enriched,
                 "--draft", LAB / "examples" / "core-public-api-draft.json"])
            return packet(repo, task, "field-view", enriched)
    if arm == "overview":
        prompt += run([sys.executable, LAB / "repo_notes.py", "view", "--repo", repo,
                       "--rev", BASE, "--manifest", manifest], text=True)
    elif arm in ("field", "field-view"):
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(str(p) for p in (repo / "packages").glob("*/src"))}
        prompt += run([sys.executable, LAB / "task_recall.py", "--repo", repo, "--rev", BASE,
                       "--manifest", manifest, "--query", TASKS[task],
                       *(["--format", "view"] if arm == "field-view" else [])], text=True, env=env)
    return prompt


def prepare(repo, trial, task, arm):
    # Every participant receives the same packages (including baseline tests) and no project history.
    body = packet(repo, task, arm)
    trial.mkdir(parents=True, exist_ok=False)
    tree = trial / "tree"
    tree.mkdir()
    scope = ["packages"]
    if task == "digest":
        scope.append("docs/architecture/module-ownership/CORE_PUBLIC_API_ALLOWLIST.json")
    archive = run(["git", "-C", repo, "archive", BASE, *scope])
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(tree, filter="data")
    run(["git", "init", "-q", tree])
    run(["git", "-C", tree, "add", *scope])
    run(["git", "-C", tree, "-c", "user.name=Trial", "-c", "user.email=trial@localhost",
         "commit", "-q", "-m", "Frozen package snapshot"])
    shutil.copyfile(HERE / "observe.py", trial / "observe.py")
    (trial / "packet.txt").write_text(body, encoding="utf-8")
    (trial / "trial.json").write_text(json.dumps({"base": BASE, "task": task, "arm": arm}), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare"])
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--trial", type=Path, required=True)
    parser.add_argument("--task", choices=TASKS, required=True)
    parser.add_argument("--arm", choices=(*ARMS, "field-repaired"), required=True)
    args = parser.parse_args()
    prepare(args.repo.resolve(), args.trial.resolve(), args.task, args.arm)


if __name__ == "__main__":
    main()
