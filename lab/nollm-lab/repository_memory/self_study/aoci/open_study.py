"""Open the published AOCI volume on its exact Git source in a new local checkout."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def run(*command: str | Path, cwd: Path | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, text=True)
    if result.returncode:
        sys.stderr.write(result.stdout)
        raise SystemExit(result.returncode)
    return result.stdout


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="New path for the verified checkout")
    parser.add_argument("--repo", type=Path, default=here.parents[4], help="Local Nollm Git repository")
    parser.add_argument("--aoci", default="aoci", help="Official AOCI executable (v0.2.0-rc2 used for the study)")
    options = parser.parse_args()
    binary = shutil.which(options.aoci)
    if binary is None:
        parser.error(f"cannot locate AOCI executable: {options.aoci}")
    binary = str(Path(binary).resolve())
    dest = options.destination.resolve()
    if dest.exists():
        parser.error(f"destination already exists: {dest}")
    study = json.loads((here / "study.json").read_text(encoding="utf-8"))
    oid = study["commit"]
    for name, expected in study["volume_sha256"].items():
        if hashlib.sha256((here / name).read_bytes()).hexdigest() != expected:
            parser.error(f"volume digest differs from study.json: {name}")

    repo = options.repo.resolve()
    if run("git", "rev-parse", oid + "^{tree}", cwd=repo).strip() != study["tree"]:
        parser.error(f"Nollm source tree unavailable at {oid}")
    run("git", "clone", "--quiet", "--no-checkout", "--local", repo, dest)
    run("git", "checkout", "--quiet", "--detach", oid, cwd=dest)
    run(binary, "init", "--scope-profile", study["scope_profile"], cwd=dest)
    # Init appends its integration block to the tracked (empty) source AGENTS.md.
    run("git", "restore", "--", "AGENTS.md", cwd=dest)
    run("git", "diff", "--exit-code", "HEAD", cwd=dest)
    for name in study["volume_sha256"]:
        shutil.copyfile(here / name, dest / name)
    run(binary, "scan", "--json", cwd=dest)
    verify = json.loads(run(binary, "verify", "--json", cwd=dest))
    check = json.loads(run(binary, "check", "--json", cwd=dest))
    governance = verify["governance"]
    drift = governance["code_drift"]
    skipped = {row["path"] for row in study["source_skip"]}
    if (not check["ok"] or not verify["governance_aligned"]
            or verify["composite_identity"] != study["terminal_proof"]["composite_identity"]
            or governance["code_source_count"] != study["tracked_sources"]
            or governance["code_entry_count"] != study["objects"]
            or set(drift["skipped"]) != skipped):
        raise SystemExit("The rebuilt checkout differs from the published AOCI study")
    print(json.dumps({"checkout": str(dest), "commit": oid, "objects": governance["code_entry_count"],
                      "skipped": sorted(skipped), "check_ok": True, "verify_aligned": True},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
