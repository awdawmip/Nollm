"""Fail closed when archived or generated assets return to the active tree."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_JSONL_BYTES = 1_048_576
JSONL_ALLOWLIST = {
    "experiments/grf/datasets/concentrated_facts.jsonl",
    "experiments/grf/datasets/false_stitch_decoys.jsonl",
    "experiments/grf/datasets/scattered_facts.jsonl",
    "lab/nollm-lab/statement_formation/datasets/statement_formation_v1.jsonl",
}
# Exact traces retained by the current EM reports and their replay commands.
RETAINED_RESEARCH_EVIDENCE = {
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/F/reads.jsonl",
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/N/reads.jsonl",
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/S/reads.jsonl",
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/followup/clean/reads/L.jsonl",
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/followup/clean/reads/N.jsonl",
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/followup/continuation/reads/F.jsonl",
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/followup/continuation/reads/N.jsonl",
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/followup/reads/F.jsonl",
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/followup/reads/L.jsonl",
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/followup/reads/N.jsonl",
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/followup/reads/P.jsonl",
    "lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/followup/reads/S.jsonl",
}
RUNS_ALLOWLIST = {
    "lab/nollm-lab/dream_agent/runs/run-live-round.ps1",
}
ARCHIVE_SUFFIXES = (".bundle", ".zip", ".tar", ".tar.gz", ".tgz", ".7z")
FORBIDDEN_PREFIXES = ("validation/live/", "validation/frozen/", "docs/delivery/")
FORBIDDEN_SEGMENTS = {"results", "runtime_truth", "receipts"}
MARKDOWN_LINK = re.compile(r"\[[^]]*\]\(([^)]+)\)")


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def local_markdown_link_errors(paths: list[str]) -> list[str]:
    tracked = set(paths)
    tracked_directories = {parent.as_posix() for path in paths for parent in Path(path).parents}
    errors: list[str] = []
    for relative in paths:
        source = ROOT / relative
        if source.suffix.lower() != ".md" or not source.is_file():
            continue
        try:
            text = source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for target in MARKDOWN_LINK.findall(text):
            target = target.split("#", 1)[0]
            if (
                not target
                or "://" in target
                or target.startswith(("#", "mailto:"))
                or "|" in target
            ):
                continue
            resolved = (source.parent / target).resolve()
            try:
                linked = resolved.relative_to(ROOT).as_posix()
            except ValueError:
                continue
            if linked not in tracked and linked not in tracked_directories:
                errors.append(f"{relative}: broken tracked Markdown link {target}")
    return errors


def validate(paths: list[str]) -> list[str]:
    errors: list[str] = []
    agents = ROOT / "AGENTS.md"
    if not agents.is_file() or not agents.read_text(encoding="utf-8").strip():
        errors.append("AGENTS.md must provide the current project entry instructions")

    for relative in paths:
        lower = relative.lower()
        parts = set(Path(relative).parts)
        if lower.endswith(ARCHIVE_SUFFIXES):
            errors.append(f"{relative}: archive or bundle is forbidden in Git")
        if lower.endswith(".baiduyun.uploading.cfg"):
            errors.append(f"{relative}: external sync sidecar is forbidden in Git")
        if relative.startswith(FORBIDDEN_PREFIXES):
            errors.append(f"{relative}: frozen evidence or delivery receipt root is forbidden")
        if parts & FORBIDDEN_SEGMENTS:
            errors.append(f"{relative}: generated asset directory is forbidden")
        if "runs" in parts and relative not in RUNS_ALLOWLIST:
            errors.append(f"{relative}: generated run directory is forbidden")
        if "DELIVERY_RECEIPT" in Path(relative).name.upper():
            errors.append(f"{relative}: delivery receipt is forbidden in the active tree")
        if (lower.endswith(".jsonl") and relative not in JSONL_ALLOWLIST
                and relative not in RETAINED_RESEARCH_EVIDENCE):
            size = (ROOT / relative).stat().st_size
            if size > MAX_TRACKED_JSONL_BYTES:
                errors.append(
                    f"{relative}: generated JSONL exceeds {MAX_TRACKED_JSONL_BYTES} bytes"
                )
            else:
                errors.append(f"{relative}: JSONL is not an allowlisted fixture or retained research evidence")

    errors.extend(local_markdown_link_errors(paths))
    return sorted(set(errors))


def main() -> int:
    paths = tracked_files()
    errors = validate(paths)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"active tree asset check: tracked={len(paths)} violations=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
