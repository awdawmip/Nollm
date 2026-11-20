"""Install a portable repository-memory skill into a new directory."""
import argparse
import os
from pathlib import Path
from shutil import copy2
import subprocess
from tempfile import TemporaryDirectory


LAB = Path(__file__).resolve().parent
REPO = LAB.parents[2]
SKILL_NAME = "nollm-repository-memory"
HOST_DIRS = {
    "codex": {"user": ".agents", "repo": ".agents"},
    "opencode": {"user": ".agents", "repo": ".agents"},
    "claude": {"user": ".claude", "repo": ".claude"},
    "copilot": {"user": ".copilot", "repo": ".github"},
}


def host_destination(host, scope, repo):
    if scope == "repo":
        result = subprocess.run(["git", "-C", str(repo or "."), "rev-parse", "--show-toplevel"],
                                capture_output=True)
        if result.returncode:
            raise ValueError("repository installation requires a Git worktree; use --repo PATH")
        root = Path(os.fsdecode(result.stdout.removesuffix(b"\n").removesuffix(b"\r")))
    else:
        root = Path.home()
    return root / HOST_DIRS[host][scope] / "skills" / SKILL_NAME


def install(destination):
    destination = Path(destination).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"destination already exists: {destination}; choose a new directory")
    source = LAB / "skills" / SKILL_NAME
    files = {source / "SKILL.md": Path("SKILL.md"),
             source / "scripts/memory.py": Path("scripts/memory.py"),
             REPO / "LICENSE": Path("LICENSE")}
    runtime = Path("scripts/runtime")
    for name in ("field_demo.py", "repo_notes.py", "task_recall.py", "facts.py", "extra_languages.py", "records.py",
                 "router.py", "query-lexicon.tsv", "machine_field.py", "check_marks.py", "language_profiles.json",
                 "aoci_rows.py", "geocode.py", "geometry_cli.py", "native_geo.py", "coverage_cli.py"):
        files[LAB / name] = runtime / name
    em = LAB / "enterprise_math"
    for path in (em / "research.py", *(em / "field").rglob("*.json")):
        files[path] = runtime / path.relative_to(LAB)
    for package in ("nollm-core", "nollm-access"):
        src = REPO / "packages" / package / "src"
        for path in (src / package.replace("-", "_")).rglob("*.py"):
            files[path] = runtime / path.relative_to(src)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent, prefix=".nollm-install-") as staging:
        root = Path(staging) / SKILL_NAME
        for path, relative in files.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            copy2(path, target)
        root.rename(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--dest", type=Path, help="new skill directory, including the skill name")
    target.add_argument("--host", choices=HOST_DIRS, help="install into a host's skill directory")
    parser.add_argument("--scope", choices=("user", "repo"), help="installation scope (default: user)")
    parser.add_argument("--repo", type=Path, help="target worktree for --scope repo (default: current directory)")
    args = parser.parse_args()
    if args.dest is not None and (args.scope or args.repo is not None):
        parser.error("--scope and --repo select host locations; use --host with these options")
    if args.repo is not None and args.scope != "repo":
        parser.error("--repo requires --scope repo")
    try:
        destination = args.dest or host_destination(args.host, args.scope or "user", args.repo)
        print(install(destination))
    except (OSError, ValueError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")


if __name__ == "__main__":
    main()
