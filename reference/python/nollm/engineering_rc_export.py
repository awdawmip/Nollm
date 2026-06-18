from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping, Sequence

SCHEMA = "nollm.engineering_rc_export_check.v1"

REQUIRED_RELEASE_FILES = (
    "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_FREEZE_20260618.md",
    "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md",
    "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EVALUATION_GUIDE_20260618.md",
    "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EXPORT_MANIFEST_20260618.md",
    "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EXPORT_MANIFEST_20260618.json",
)

CANONICAL_COMMANDS = (
    "python scripts/check_engineering_rc_export.py",
    "python scripts/run_nollm_local_gate.py --skip-pytest",
    "python scripts/run_g_series_engineering_gate.py",
    "python scripts/run_dream_golden_regression.py",
    "python -m pytest -q tests/test_engineering_rc_export.py tests/test_g_series_engineering_closure.py tests/test_minimal_ablation_experiment.py tests/test_mode3_trace_experiment.py tests/test_gravity.py",
)

FORBIDDEN_SEMANTICS = (
    "stable recall surface enabled",
    "hard drift rejection",
    "automatic writeback",
    "anchor creation enabled",
    "drift_class maps to trust",
    "Nollm is proven long-term memory",
)

MANIFEST_LIST_FIELDS = (
    "read_first",
    "implementation_modules",
    "tests",
    "runtime_reports",
)


def build_engineering_rc_export_check(repo_root: Path) -> dict[str, object]:
    repo_root = Path(repo_root).resolve()
    failures: list[str] = []

    checked_files = list(REQUIRED_RELEASE_FILES)
    _check_required_files(repo_root, REQUIRED_RELEASE_FILES, failures)

    manifest_path = repo_root / "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EXPORT_MANIFEST_20260618.json"
    manifest = _read_manifest(manifest_path, failures)
    manifest_paths = _manifest_paths(manifest, failures)
    checked_files.extend(manifest_paths)
    _check_required_files(repo_root, manifest_paths, failures)

    audit_reports = _audit_generated_reports(repo_root / "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md")
    checked_files.extend(audit_reports)
    _check_required_files(repo_root, audit_reports, failures)

    guide_text = _read_text(repo_root / "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EVALUATION_GUIDE_20260618.md")
    checked_commands = list(CANONICAL_COMMANDS)
    for command in CANONICAL_COMMANDS:
        if command not in guide_text:
            failures.append(f"missing_evaluation_command:{command}")

    release_text = "\n".join(_read_text(repo_root / path) for path in REQUIRED_RELEASE_FILES if (repo_root / path).exists())
    forbidden = {phrase: (phrase.lower() in release_text.lower()) for phrase in FORBIDDEN_SEMANTICS}
    for phrase, present in forbidden.items():
        if present:
            failures.append(f"forbidden_semantics:{phrase}")

    if "conversation_backups/" in release_text or "conversation_backups" in json.dumps(manifest, sort_keys=True):
        failures.append("conversation_backups_listed_as_release_artifact")

    report = {
        "schema": SCHEMA,
        "ok": not failures,
        "failures": sorted(failures),
        "checked_files": sorted(dict.fromkeys(checked_files)),
        "checked_commands": checked_commands,
        "forbidden_semantics": forbidden,
    }
    _assert_json_primitive(report)
    return report


def write_engineering_rc_export_check(report: Mapping[str, object], output: Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_json_dumps(report), encoding="utf-8", newline="\n")


def engineering_rc_export_check_json(report: Mapping[str, object]) -> str:
    return _json_dumps(report)


def _read_manifest(path: Path, failures: list[str]) -> Mapping[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid_manifest_json:{exc.msg}")
        return {}
    if not isinstance(data, Mapping):
        failures.append("invalid_manifest_json:not_object")
        return {}
    return data


def _manifest_paths(manifest: Mapping[str, object], failures: list[str]) -> list[str]:
    paths: list[str] = []
    for field in MANIFEST_LIST_FIELDS:
        value = manifest.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            failures.append(f"invalid_manifest_field:{field}")
            continue
        paths.extend(value)
    return paths


def _audit_generated_reports(path: Path) -> list[str]:
    text = _read_text(path)
    marker = "## Expected Generated Reports"
    if marker not in text:
        return []
    section = text.split(marker, 1)[1]
    match = re.search(r"```text\n(.*?)\n```", section, flags=re.DOTALL)
    if not match:
        return []
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def _check_required_files(repo_root: Path, paths: Sequence[str], failures: list[str]) -> None:
    for path in paths:
        if not (repo_root / path).exists():
            failures.append(f"missing_path:{path}")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _json_dumps(report: Mapping[str, object]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def _assert_json_primitive(value: object) -> None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, list):
        for item in value:
            _assert_json_primitive(item)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("report keys must be strings")
            _assert_json_primitive(item)
        return
    raise TypeError(f"report value is not JSON primitive: {type(value).__name__}")


__all__ = [
    "CANONICAL_COMMANDS",
    "FORBIDDEN_SEMANTICS",
    "REQUIRED_RELEASE_FILES",
    "SCHEMA",
    "build_engineering_rc_export_check",
    "engineering_rc_export_check_json",
    "write_engineering_rc_export_check",
]
