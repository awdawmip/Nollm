from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from nollm.dream_checks_manifest import build_all_dream_checks_manifest
from nollm.dream_corpus_dry_run import run_real_corpus_dry_run
from nollm.dream_suite import build_dream_geometry_suite_report
from nollm.local_gate import build_local_gate_report

GOLDEN_REPORTS = {
    "dream_suite_report": "examples/openclaw_dream/golden/dream_suite_report.golden.json",
    "all_dream_checks_manifest": "examples/openclaw_dream/golden/all_dream_checks_manifest.golden.json",
    "real_corpus_dry_run_report": "examples/openclaw_dream/golden/real_corpus_dry_run_report.golden.json",
    "local_gate_report": "examples/openclaw_dream/golden/local_gate_report.golden.json",
}

REGRESSION_WARNINGS = (
    "E8 is an internal regression guard",
    "E8 is not a stable V1 recall/tool surface",
)

NOISY_KEYS = frozenset(
    {
        "generated_at",
        "timestamp",
        "duration",
        "duration_seconds",
        "elapsed",
        "elapsed_seconds",
        "runtime_cache_cleanup",
    }
)


def run_golden_regression(repo_root: Path | str, update: bool = False) -> dict[str, object]:
    root = Path(repo_root).resolve()
    current = _current_reports(root)
    reports: dict[str, object] = {}
    failed = 0
    for name in sorted(GOLDEN_REPORTS):
        golden_rel = GOLDEN_REPORTS[name]
        golden_path = root / golden_rel
        normalized = normalize_report(current[name], root)
        if update:
            _write_json(golden_path, normalized)
            reports[name] = {
                "ok": True,
                "golden_path": golden_rel,
                "matched": True,
                "updated": True,
            }
            continue
        if not golden_path.exists():
            failed += 1
            reports[name] = {
                "ok": False,
                "golden_path": golden_rel,
                "matched": False,
                "reason": "missing golden",
                "summary": "golden file is absent",
            }
            continue
        golden = json.loads(golden_path.read_text(encoding="utf-8"))
        matched = golden == normalized
        if not matched:
            failed += 1
        reports[name] = {
            "ok": matched,
            "golden_path": golden_rel,
            "matched": matched,
            "reason": "" if matched else "golden mismatch",
            "summary": "" if matched else _mismatch_summary(golden, normalized),
        }

    result = {
        "schema": "nollm.dream_golden_regression.v1",
        "status": "experimental_internal_only",
        "ok": failed == 0,
        "update": update,
        "reports": reports,
        "failed_report_count": failed,
        "warnings": list(REGRESSION_WARNINGS),
    }
    validate_golden_regression_result(result)
    return result


def normalize_report(report: object, repo_root: Path | str | None = None) -> object:
    root = Path(repo_root).resolve() if repo_root is not None else None
    return _normalize_value(report, root)


def write_golden_regression_result(result: Mapping[str, object], output_path: Path | str) -> None:
    validate_golden_regression_result(result)
    _write_json(Path(output_path), result)


def validate_golden_regression_result(result: Mapping[str, object]) -> None:
    if not isinstance(result, Mapping):
        raise ValueError("golden regression result must be a mapping")
    for key in ("schema", "status", "ok", "update", "reports", "failed_report_count", "warnings"):
        if key not in result:
            raise ValueError(f"missing golden regression result field: {key}")
    if result["schema"] != "nollm.dream_golden_regression.v1":
        raise ValueError("unsupported golden regression schema")
    if result["status"] != "experimental_internal_only":
        raise ValueError("golden regression status must be experimental_internal_only")
    if not _is_json_primitive(result):
        raise ValueError("golden regression result must be JSON-primitive serializable")


def _current_reports(root: Path) -> dict[str, object]:
    return {
        "dream_suite_report": build_dream_geometry_suite_report(root),
        "real_corpus_dry_run_report": run_real_corpus_dry_run(root),
        "all_dream_checks_manifest": build_all_dream_checks_manifest(root),
        "local_gate_report": build_local_gate_report(root, include_pytest=False),
    }


def _normalize_value(value: object, root: Path | None) -> object:
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_value(item, root)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if str(key) not in NOISY_KEYS
        }
    if isinstance(value, list):
        return [_normalize_value(item, root) for item in value]
    if isinstance(value, str):
        normalized = value.replace("\\", "/")
        if root is not None:
            normalized = normalized.replace(root.as_posix(), "<repo>")
            normalized = normalized.replace(str(root).replace("\\", "/"), "<repo>")
        return normalized
    return value


def _mismatch_summary(golden: object, current: object) -> str:
    if type(golden) is not type(current):
        return f"type changed: {type(golden).__name__} -> {type(current).__name__}"
    if isinstance(golden, Mapping) and isinstance(current, Mapping):
        golden_keys = set(golden.keys())
        current_keys = set(current.keys())
        if golden_keys != current_keys:
            return f"keys changed: missing={sorted(golden_keys - current_keys)} added={sorted(current_keys - golden_keys)}"
        for key in sorted(golden_keys):
            if golden[key] != current[key]:
                return f"value changed at key={key}"
    return "content changed"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _is_json_primitive(value: object) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_primitive(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_primitive(item) for key, item in value.items())
    return False


__all__ = [
    "GOLDEN_REPORTS",
    "REGRESSION_WARNINGS",
    "run_golden_regression",
    "normalize_report",
    "write_golden_regression_result",
    "validate_golden_regression_result",
]
