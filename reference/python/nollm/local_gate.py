from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from nollm.dream_checks_manifest import build_all_dream_checks_manifest
from nollm.dream_triage import build_dream_triage_report

GATE_WARNINGS = (
    "E7 is an internal local gate",
    "E7 is not a stable V1 recall/tool surface",
)

FORBIDDEN_FLAG_KEYS = (
    "parent_child",
    "anchor_ownership",
    "folder_tree",
    "confirmed_placement",
)

RUNTIME_CACHE_DIR_NAMES = frozenset({".pytest_cache", "__pycache__"})


@dataclass(frozen=True)
class GateComponent:
    ok: bool
    included: bool = True
    returncode: int = 0
    detail: str = ""
    timeout_seconds: int = 0

    def to_record(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "included": self.included,
            "returncode": self.returncode,
            "detail": self.detail,
            "timeout_seconds": self.timeout_seconds,
        }


def build_local_gate_report(
    repo_root: Path | str,
    *,
    include_pytest: bool = False,
    pytest_timeout_seconds: int = 120,
) -> dict[str, object]:
    root = Path(repo_root).resolve()
    reference_python = root / "reference" / "python"
    before_removed = cleanup_runtime_cache_artifacts(root)
    package_hygiene = _run_component(
        [
            sys.executable,
            str(reference_python / "scripts" / "check_package_hygiene.py"),
            str(root),
        ],
        cwd=reference_python,
        detail="package hygiene",
    )
    dream_manifest = _dream_manifest_component(root)
    dream_triage = _dream_triage_component(root)
    if include_pytest:
        before_removed.extend(cleanup_runtime_cache_artifacts(root))
        pytest_component = _run_component(
            [sys.executable, "run_tests.py"],
            cwd=reference_python,
            detail="pytest",
            timeout_seconds=pytest_timeout_seconds,
        )
    else:
        pytest_component = GateComponent(
            ok=True,
            included=False,
            detail="pytest skipped",
            timeout_seconds=pytest_timeout_seconds,
        )
    after_removed = cleanup_runtime_cache_artifacts(root)

    components = {
        "package_hygiene": package_hygiene.to_record(),
        "dream_checks_manifest": dream_manifest.to_record(),
        "dream_failure_triage": dream_triage.to_record(),
        "pytest": pytest_component.to_record(),
    }
    forbidden_semantics = _forbidden_semantics_from_manifest(root)
    ok = all(bool(component["ok"]) for component in components.values()) and not any(
        forbidden_semantics.values()
    )
    report = {
        "schema": "nollm.local_gate.v1",
        "status": "experimental_internal_only",
        "ok": ok,
        "components": components,
        "runtime_cache_cleanup": {
            "before_count": len(before_removed),
            "after_count": len(after_removed),
            "removed_paths": sorted(set(before_removed).union(after_removed)),
        },
        "forbidden_semantics": forbidden_semantics,
        "warnings": list(GATE_WARNINGS),
    }
    validate_local_gate_report(report)
    return report


def aggregate_local_gate_report(
    components: Mapping[str, Mapping[str, object]],
    forbidden_semantics: Mapping[str, bool],
) -> dict[str, object]:
    flags = {key: bool(forbidden_semantics.get(key, False)) for key in FORBIDDEN_FLAG_KEYS}
    ok = all(bool(component.get("ok", False)) for component in components.values()) and not any(flags.values())
    report = {
        "schema": "nollm.local_gate.v1",
        "status": "experimental_internal_only",
        "ok": ok,
        "components": dict(components),
        "runtime_cache_cleanup": {
            "before_count": 0,
            "after_count": 0,
            "removed_paths": [],
        },
        "forbidden_semantics": flags,
        "warnings": list(GATE_WARNINGS),
    }
    validate_local_gate_report(report)
    return report


def validate_local_gate_report(report: Mapping[str, object]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("local gate report must be a mapping")
    for key in (
        "schema",
        "status",
        "ok",
        "components",
        "runtime_cache_cleanup",
        "forbidden_semantics",
        "warnings",
    ):
        if key not in report:
            raise ValueError(f"missing local gate report field: {key}")
    if report["schema"] != "nollm.local_gate.v1":
        raise ValueError("unsupported local gate schema")
    if report["status"] != "experimental_internal_only":
        raise ValueError("local gate status must be experimental_internal_only")
    if not _is_json_primitive(report):
        raise ValueError("local gate report must be JSON-primitive serializable")


def write_local_gate_report(report: Mapping[str, object], output_path: Path | str) -> None:
    validate_local_gate_report(report)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _dream_manifest_component(root: Path) -> GateComponent:
    try:
        manifest = build_all_dream_checks_manifest(root)
    except Exception as exc:
        return GateComponent(ok=False, returncode=1, detail=f"dream checks manifest failed: {exc}")
    return GateComponent(
        ok=bool(manifest["ok"]),
        returncode=0 if manifest["ok"] else 1,
        detail="dream checks manifest",
    )


def _dream_triage_component(root: Path) -> GateComponent:
    try:
        triage = build_dream_triage_report(root, ignored_reports=("local_gate",))
    except Exception as exc:
        return GateComponent(ok=False, returncode=1, detail=f"dream failure triage failed: {exc}")
    return GateComponent(
        ok=bool(triage["ok"]),
        returncode=0 if triage["ok"] else 1,
        detail="dream failure triage",
    )


def _forbidden_semantics_from_manifest(root: Path) -> dict[str, bool]:
    try:
        manifest = build_all_dream_checks_manifest(root)
        flags = manifest.get("forbidden_semantics", {})
    except Exception:
        flags = {}
    if not isinstance(flags, Mapping):
        flags = {}
    return {key: bool(flags.get(key, False)) for key in FORBIDDEN_FLAG_KEYS}


def _run_component(
    command: list[str],
    *,
    cwd: Path,
    detail: str,
    timeout_seconds: int = 120,
) -> GateComponent:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return GateComponent(
            ok=False,
            returncode=-1,
            detail=f"{detail} timed out",
            timeout_seconds=timeout_seconds,
        )
    except Exception as exc:
        return GateComponent(
            ok=False,
            returncode=1,
            detail=f"{detail} failed: {exc}",
            timeout_seconds=timeout_seconds,
        )
    return GateComponent(
        ok=result.returncode == 0,
        returncode=int(result.returncode),
        detail=detail,
        timeout_seconds=timeout_seconds,
    )


def cleanup_runtime_cache_artifacts(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    matches: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if relative == ".git" or relative.startswith(".git/"):
            continue
        if path.is_dir() and path.name in RUNTIME_CACHE_DIR_NAMES:
            matches.add(relative)
        elif path.is_file() and path.suffix == ".pyc":
            matches.add(relative)

    for relative in sorted(matches, key=lambda item: (item.count("/"), item), reverse=True):
        path = root / relative
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    return sorted(matches)


def _is_json_primitive(value: object) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_primitive(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_primitive(item) for key, item in value.items())
    return False


__all__ = [
    "GATE_WARNINGS",
    "GateComponent",
    "aggregate_local_gate_report",
    "build_local_gate_report",
    "cleanup_runtime_cache_artifacts",
    "validate_local_gate_report",
    "write_local_gate_report",
]
