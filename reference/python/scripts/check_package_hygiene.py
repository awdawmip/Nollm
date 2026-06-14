from __future__ import annotations

import sys
from pathlib import Path


BLOCKED_DIR_NAMES = {".pytest_cache", "__pycache__"}
BLOCKED_FILE_NAMES = {"settings.json", "audit.json", "audit.md"}
BLOCKED_SUFFIXES = {".pyc", ".zip", ".tar", ".tgz"}
BLOCKED_MULTI_SUFFIXES = {".tar.gz"}
BLOCKED_PATTERNS = (
    "examples/openclaw/recalls/recall_*.json",
    "examples/openclaw/recalls/recall_*.md",
    "*_audit.json",
    "*_audit.md",
)
ALLOWED_RELATIVE_PATHS = {
    "examples/audit_reports/openclaw_audit.json",
    "examples/openclaw/recalls/sample_recall_digest.json",
    "examples/openclaw/recalls/sample_recall_digest.md",
}


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    root = Path(args[0]).resolve() if args else Path(__file__).resolve().parents[3]
    issues = find_issues(root)
    if issues:
        print("FAIL package hygiene")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("PASS package hygiene")
    return 0


def find_issues(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if ".git/" in relative or relative == ".git":
            continue
        if relative in ALLOWED_RELATIVE_PATHS:
            continue
        if path.is_dir() and path.name in BLOCKED_DIR_NAMES:
            issues.append(relative)
        elif path.is_file() and is_blocked_file(path, relative):
            issues.append(relative)
    for pattern in BLOCKED_PATTERNS:
        for path in root.glob(pattern):
            relative = path.relative_to(root).as_posix()
            if relative not in ALLOWED_RELATIVE_PATHS:
                issues.append(relative)
    return sorted(set(issues))


def is_blocked_file(path: Path, relative: str) -> bool:
    if path.name in BLOCKED_FILE_NAMES:
        return True
    if path.suffix in BLOCKED_SUFFIXES:
        return True
    return any(relative.endswith(suffix) for suffix in BLOCKED_MULTI_SUFFIXES)


if __name__ == "__main__":
    raise SystemExit(main())
