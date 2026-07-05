from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence
import zipfile

from nollm.engineering_rc_export import HASH_MANIFEST_PATH, EXPORT_MANIFEST_PATH, canonical_rc_artifact_bytes

SCHEMA = "nollm.engineering_rc_archive.v1"
FIXED_ZIP_TIMESTAMP = (2026, 6, 18, 0, 0, 0)
RUNTIME_PREFIX = "out/nollm_runtime/"


def build_engineering_rc_export_archive(
    repo_root: Path,
    output: Path,
    *,
    allow_non_runtime_output: bool = False,
) -> dict[str, object]:
    repo_root = Path(repo_root).resolve()
    output = Path(output).resolve()
    failures = _validate_output_path(repo_root, output, allow_non_runtime_output)
    expected = _expected_artifacts(repo_root, failures)
    if failures:
        return _archive_report(output, [], failures)

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for path, record in expected.items():
            try:
                data = canonical_rc_artifact_bytes(repo_root, path)
            except ValueError as exc:
                failures.append(str(exc))
                continue
            if len(data) != record["size_bytes"]:
                failures.append(f"source_size_mismatch:{path}")
            if hashlib.sha256(data).hexdigest() != record["sha256"]:
                failures.append(f"source_sha256_mismatch:{path}")
            if failures:
                continue
            info = zipfile.ZipInfo(path, FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)

    if failures:
        output.unlink(missing_ok=True)
        return _archive_report(output, list(expected), failures)
    return verify_engineering_rc_export_archive(repo_root, output)


def verify_engineering_rc_export_archive(repo_root: Path, archive_path: Path) -> dict[str, object]:
    repo_root = Path(repo_root).resolve()
    archive_path = Path(archive_path).resolve()
    failures: list[str] = []
    expected = _expected_artifacts(repo_root, failures)
    if not archive_path.exists():
        failures.append(f"archive_missing:{archive_path}")
        return _archive_report(archive_path, list(expected), failures)

    try:
        _validate_raw_zip_entry_names(archive_path, failures)
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            for name in names:
                _validate_archive_entry_name(name, failures)
            if names != sorted(names):
                failures.append("archive_entries_not_sorted")
            if len(names) != len(set(names)):
                failures.append("archive_duplicate_entries")
            expected_names = sorted(expected)
            if sorted(names) != expected_names:
                for name in sorted(set(expected_names) - set(names)):
                    failures.append(f"archive_missing_entry:{name}")
                for name in sorted(set(names) - set(expected_names)):
                    failures.append(f"archive_unexpected_entry:{name}")
            for name in names:
                if name not in expected:
                    continue
                data = archive.read(name)
                record = expected[name]
                if len(data) != record["size_bytes"]:
                    failures.append(f"archive_size_mismatch:{name}")
                if hashlib.sha256(data).hexdigest() != record["sha256"]:
                    failures.append(f"archive_sha256_mismatch:{name}")
    except zipfile.BadZipFile:
        failures.append("archive_bad_zip")

    return _archive_report(archive_path, sorted(expected), failures)


def write_engineering_rc_archive_report(report: Mapping[str, object], output: Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _expected_artifacts(repo_root: Path, failures: list[str]) -> dict[str, Mapping[str, object]]:
    manifest_path = repo_root / HASH_MANIFEST_PATH
    if not manifest_path.exists():
        failures.append(f"missing_hash_manifest:{HASH_MANIFEST_PATH}")
        return {}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        failures.append("invalid_hash_manifest_artifacts")
        return {}
    expected: dict[str, Mapping[str, object]] = {}
    for item in artifacts:
        if not isinstance(item, Mapping):
            failures.append("invalid_hash_manifest_artifact")
            continue
        path = item.get("path")
        if not isinstance(path, str):
            failures.append("invalid_hash_manifest_artifact_path")
            continue
        _validate_archive_entry_name(path, failures)
        _validate_no_forbidden_archive_path(path, failures)
        if not (repo_root / path).exists():
            failures.append(f"source_missing:{path}")
        expected[path] = item
    if list(expected) != sorted(expected):
        failures.append("hash_manifest_artifacts_not_sorted")
    return dict(sorted(expected.items()))


def _validate_output_path(repo_root: Path, output: Path, allow_non_runtime_output: bool) -> list[str]:
    if allow_non_runtime_output:
        return []
    try:
        relative = output.relative_to(repo_root)
    except ValueError:
        return [f"output_outside_repo:{output}"]
    normalized = relative.as_posix()
    if not normalized.startswith(RUNTIME_PREFIX):
        return [f"output_not_runtime_path:{normalized}"]
    return []


def _validate_archive_entry_name(name: str, failures: list[str]) -> None:
    if "\\" in name:
        failures.append(f"archive_backslash_entry:{name}")
    if name.startswith("/") or (len(name) >= 2 and name[1] == ":"):
        failures.append(f"archive_absolute_entry:{name}")
    parts = name.replace("\\", "/").split("/")
    if ".." in parts:
        failures.append(f"archive_path_traversal_entry:{name}")


def _validate_raw_zip_entry_names(path: Path, failures: list[str]) -> None:
    data = path.read_bytes()
    signature = b"\x50\x4b\x01\x02"
    offset = 0
    while True:
        index = data.find(signature, offset)
        if index < 0:
            return
        if index + 46 > len(data):
            failures.append("archive_malformed_central_directory")
            return
        name_len = int.from_bytes(data[index + 28 : index + 30], "little")
        extra_len = int.from_bytes(data[index + 30 : index + 32], "little")
        comment_len = int.from_bytes(data[index + 32 : index + 34], "little")
        name_bytes = data[index + 46 : index + 46 + name_len]
        if b"\\" in name_bytes:
            name = name_bytes.decode("utf-8", errors="replace")
            failures.append(f"archive_backslash_entry:{name}")
        offset = index + 46 + name_len + extra_len + comment_len


def _validate_no_forbidden_archive_path(path: str, failures: list[str]) -> None:
    normalized = path.replace("\\", "/")
    parts = normalized.split("/")
    if normalized.startswith(".git/"):
        failures.append(f"archive_forbidden_entry:{path}")
    if normalized.startswith("conversation_backups/"):
        failures.append(f"archive_forbidden_entry:{path}")
    if "__pycache__" in parts or ".pytest_cache" in parts:
        failures.append(f"archive_forbidden_entry:{path}")
    if normalized.endswith(".pyc"):
        failures.append(f"archive_forbidden_entry:{path}")
    if normalized.endswith(".zip"):
        failures.append(f"archive_forbidden_entry:{path}")


def _archive_report(archive_path: Path, entries: Sequence[str], failures: Sequence[str]) -> dict[str, object]:
    archive_path = Path(archive_path)
    exists = archive_path.exists()
    data = archive_path.read_bytes() if exists else b""
    return {
        "schema": SCHEMA,
        "ok": len(failures) == 0,
        "archive_path": str(archive_path),
        "entry_count": len(entries),
        "archive_sha256": hashlib.sha256(data).hexdigest() if exists else None,
        "archive_size_bytes": len(data) if exists else 0,
        "manifest_path": EXPORT_MANIFEST_PATH,
        "hash_manifest_path": HASH_MANIFEST_PATH,
        "failures": sorted(failures),
    }


__all__ = [
    "SCHEMA",
    "build_engineering_rc_export_archive",
    "verify_engineering_rc_export_archive",
    "write_engineering_rc_archive_report",
]
