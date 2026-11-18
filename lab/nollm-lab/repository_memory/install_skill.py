"""Install a portable repository-memory skill into a new directory."""
import argparse
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory


LAB = Path(__file__).resolve().parent
REPO = LAB.parents[2]
SKILL_NAME = "nollm-repository-memory"


def install(destination):
    destination = Path(destination).expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError(f"destination already exists: {destination}; choose a new directory")
    source = LAB / "skills" / SKILL_NAME
    files = {source / "SKILL.md": Path("SKILL.md"),
             source / "scripts/memory.py": Path("scripts/memory.py"),
             REPO / "LICENSE": Path("LICENSE")}
    runtime = Path("scripts/runtime")
    for name in ("field_demo.py", "repo_notes.py", "task_recall.py"):
        files[LAB / name] = runtime / name
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
    parser.add_argument("--dest", required=True, type=Path,
                        help="new skill directory, including the skill name")
    args = parser.parse_args()
    try:
        print(install(args.dest))
    except (OSError, ValueError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")


if __name__ == "__main__":
    main()
