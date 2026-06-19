from __future__ import annotations

import json
import re
import hashlib
from pathlib import Path
from typing import Mapping, Sequence

SCHEMA = "nollm.engineering_rc_export_check.v1"
HASH_SCHEMA = "nollm.engineering_gravity_rc_artifact_hashes.v1"
HASH_MANIFEST_PATH = "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_ARTIFACT_HASHES_20260618.json"
EXPORT_MANIFEST_PATH = "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EXPORT_MANIFEST_20260618.json"

REQUIRED_RELEASE_FILES = (
    "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_FREEZE_20260618.md",
    "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md",
    "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EVALUATION_GUIDE_20260618.md",
    "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_EXPORT_MANIFEST_20260618.md",
    EXPORT_MANIFEST_PATH,
    HASH_MANIFEST_PATH,
)

CANONICAL_COMMANDS = (
    "python scripts/check_engineering_rc_export.py",
    "python scripts/run_engineering_rc_final_smoke.py",
    "python scripts/check_engineering_rc_export.py --write-hashes",
    "python scripts/build_engineering_rc_export_archive.py --output ../../out/nollm_runtime/releases/nollm_engineering_gravity_rc.zip --report ../../out/nollm_runtime/engineering_rc_archive_report.json",
    "python scripts/build_engineering_rc_export_archive.py --verify ../../out/nollm_runtime/releases/nollm_engineering_gravity_rc.zip",
    "python scripts/run_nollm_test_shards.py --list-profiles",
    "python scripts/run_nollm_test_shards.py --profile shard_smoke --timeout 20",
    "python scripts/run_nollm_test_shards.py --profile core --timeout 60",
    "python scripts/run_nollm_test_shards.py --profile docs --timeout 60",
    "python scripts/run_nollm_local_gate.py --skip-pytest",
    "python scripts/run_g_series_engineering_gate.py",
    "python scripts/run_dream_golden_regression.py",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_engineering_rc_export.py tests/test_g_series_engineering_closure.py tests/test_minimal_ablation_experiment.py tests/test_mode3_trace_experiment.py tests/test_gravity.py",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_engineering_rc_artifact_hashes.py",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_engineering_rc_archive.py",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_nollm_test_shards.py",
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

    manifest_path = repo_root / EXPORT_MANIFEST_PATH
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

    if "conversation_backups" in json.dumps(manifest, sort_keys=True):
        failures.append("conversation_backups_listed_as_release_artifact")

    hash_manifest = _read_hash_manifest(repo_root / HASH_MANIFEST_PATH, failures)
    hash_check = _check_hash_manifest(repo_root, hash_manifest, manifest_paths, failures) if hash_manifest else {}

    report = {
        "schema": SCHEMA,
        "ok": not failures,
        "failures": sorted(failures),
        "checked_files": sorted(dict.fromkeys(checked_files)),
        "checked_commands": checked_commands,
        "forbidden_semantics": forbidden,
        "hash_manifest": hash_check,
    }
    _assert_json_primitive(report)
    return report


def build_engineering_rc_artifact_hash_manifest(repo_root: Path) -> dict[str, object]:
    repo_root = Path(repo_root).resolve()
    artifact_paths = _hash_artifact_paths(repo_root)
    artifacts = [_artifact_record(repo_root, path) for path in artifact_paths]
    manifest = {
        "schema": HASH_SCHEMA,
        "date": "2026-06-18",
        "status": "experimental_internal_only",
        "claim": "testable_not_proven",
        "source_manifest": EXPORT_MANIFEST_PATH,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "excluded_local_paths": [
            ".git/",
            "__pycache__/",
            ".pytest_cache/",
            "conversation_backups/",
            "*.pyc",
            "*.zip",
        ],
    }
    _assert_json_primitive(manifest)
    return manifest


def write_engineering_rc_artifact_hash_manifest(repo_root: Path, output: Path | None = None) -> dict[str, object]:
    repo_root = Path(repo_root).resolve()
    manifest = build_engineering_rc_artifact_hash_manifest(repo_root)
    target = repo_root / HASH_MANIFEST_PATH if output is None else Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_json_dumps(manifest), encoding="utf-8", newline="\n")
    return manifest


def write_engineering_rc_export_check(report: Mapping[str, object], output: Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_json_dumps(report), encoding="utf-8", newline="\n")


def engineering_rc_export_check_json(report: Mapping[str, object]) -> str:
    return _json_dumps(report)


def _hash_artifact_paths(repo_root: Path) -> list[str]:
    failures: list[str] = []
    manifest = _read_manifest(repo_root / EXPORT_MANIFEST_PATH, failures)
    paths: set[str] = set(REQUIRED_RELEASE_FILES)
    paths.discard(HASH_MANIFEST_PATH)
    paths.update(_manifest_paths(manifest, failures))
    paths.update(_audit_generated_reports(repo_root / "docs/releases/NOLLM_ENGINEERING_GRAVITY_RC_AUDIT_20260618.md"))
    paths.update(_command_module_paths())
    paths.update(_command_script_paths())
    paths.update(_command_test_paths())
    return sorted(path for path in paths if not _is_excluded_hash_path(path))


def _command_module_paths() -> list[str]:
    return [
        "reference/python/nollm/engineering_rc_archive.py",
        "reference/python/nollm/engineering_rc_export.py",
        "reference/python/nollm/engineering_rc_final_smoke.py",
        "reference/python/nollm/pytest_env.py",
    ]


def _command_script_paths() -> list[str]:
    return [
        "reference/python/scripts/check_engineering_rc_export.py",
        "reference/python/scripts/build_engineering_rc_export_archive.py",
        "reference/python/scripts/run_engineering_rc_final_smoke.py",
        "reference/python/scripts/run_nollm_test_shards.py",
        "reference/python/scripts/run_nollm_local_gate.py",
        "reference/python/scripts/run_g_series_engineering_gate.py",
        "reference/python/scripts/run_dream_golden_regression.py",
    ]


def _command_test_paths() -> list[str]:
    return [
        "reference/python/tests/test_engineering_rc_artifact_hashes.py",
        "reference/python/tests/test_engineering_rc_archive.py",
        "reference/python/tests/test_engineering_rc_export.py",
        "reference/python/tests/test_engineering_rc_final_smoke.py",
        "reference/python/tests/test_nollm_test_shards.py",
        "reference/python/tests/test_test_shards.py",
        "reference/python/tests/test_g_series_engineering_closure.py",
        "reference/python/tests/test_minimal_ablation_experiment.py",
        "reference/python/tests/test_mode3_trace_experiment.py",
        "reference/python/tests/test_gravity.py",
    ]


def _artifact_record(repo_root: Path, path: str) -> dict[str, object]:
    target = repo_root / path
    data = target.read_bytes()
    return {
        "path": path,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _read_hash_manifest(path: Path, failures: list[str]) -> Mapping[str, object]:
    if not path.exists():
        failures.append(f"missing_path:{HASH_MANIFEST_PATH}")
        return {}
    data = _read_manifest(path, failures)
    if data and data.get("schema") != HASH_SCHEMA:
        failures.append("invalid_hash_manifest_schema")
    return data


def _check_hash_manifest(
    repo_root: Path,
    hash_manifest: Mapping[str, object],
    manifest_paths: Sequence[str],
    failures: list[str],
) -> dict[str, object]:
    artifacts = hash_manifest.get("artifacts")
    if not isinstance(artifacts, list) or not all(isinstance(item, Mapping) for item in artifacts):
        failures.append("invalid_hash_manifest_artifacts")
        return {"validated": False, "artifact_count": 0}

    paths = [str(item.get("path")) for item in artifacts]
    if paths != sorted(paths):
        failures.append("hash_manifest_not_sorted")
    if len(paths) != len(set(paths)):
        failures.append("hash_manifest_duplicate_paths")
    if hash_manifest.get("artifact_count") != len(artifacts):
        failures.append("hash_manifest_artifact_count_mismatch")

    covered = set(paths)
    expected = set(_hash_artifact_paths(repo_root))
    for path in sorted(expected - covered):
        failures.append(f"hash_manifest_missing_artifact:{path}")
    for path in sorted(covered - expected):
        failures.append(f"hash_manifest_unexpected_artifact:{path}")
    for path in manifest_paths:
        if path not in covered and not _is_excluded_hash_path(path):
            failures.append(f"export_manifest_path_not_hashed:{path}")

    forbidden_paths = [path for path in paths if _is_excluded_hash_path(path)]
    for path in forbidden_paths:
        failures.append(f"hash_manifest_forbidden_artifact:{path}")

    for item in artifacts:
        path = item.get("path")
        if not isinstance(path, str):
            failures.append("hash_manifest_artifact_missing_path")
            continue
        target = repo_root / path
        if not target.exists():
            failures.append(f"hash_manifest_missing_file:{path}")
            continue
        expected_record = _artifact_record(repo_root, path)
        if item.get("size_bytes") != expected_record["size_bytes"]:
            failures.append(f"hash_manifest_size_mismatch:{path}")
        if item.get("sha256") != expected_record["sha256"]:
            failures.append(f"hash_manifest_sha256_mismatch:{path}")

    return {
        "validated": True,
        "artifact_count": len(artifacts),
        "path": HASH_MANIFEST_PATH,
    }


def _is_excluded_hash_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    return (
        normalized.startswith(".git/")
        or normalized.startswith("conversation_backups/")
        or normalized.endswith(".pyc")
        or normalized.endswith(".zip")
        or "__pycache__" in parts
        or ".pytest_cache" in parts
    )


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
    "HASH_MANIFEST_PATH",
    "HASH_SCHEMA",
    "REQUIRED_RELEASE_FILES",
    "SCHEMA",
    "build_engineering_rc_artifact_hash_manifest",
    "build_engineering_rc_export_check",
    "engineering_rc_export_check_json",
    "write_engineering_rc_artifact_hash_manifest",
    "write_engineering_rc_export_check",
]
