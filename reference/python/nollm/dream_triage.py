from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

TRIAGE_REPORTS = {
    "dream_suite": "examples/openclaw_dream/dream_suite_report.json",
    "real_corpus_dry_run": "examples/openclaw_dream/real_corpus_dry_run_report.json",
    "all_dream_checks_manifest": "examples/openclaw_dream/all_dream_checks_manifest.json",
    "local_gate": "examples/openclaw_dream/local_gate_report.json",
    "golden_regression": "examples/openclaw_dream/golden_regression_report.json",
}

FORBIDDEN_FLAGS = (
    "parent_child",
    "anchor_ownership",
    "folder_tree",
    "confirmed_placement",
)

TRIAGE_WARNINGS = (
    "E9 is an internal triage report.",
    "E9 is not a stable V1 recall/tool surface.",
)


def build_dream_triage_report(repo_root: Path | str) -> dict[str, object]:
    root = Path(repo_root)
    reports: dict[str, object] = {}
    forbidden = {key: False for key in FORBIDDEN_FLAGS}
    missing = 0
    failed = 0

    for name, rel_path in TRIAGE_REPORTS.items():
        path = root / rel_path
        if not path.exists():
            missing += 1
            failed += 1
            reports[name] = {
                "present": False,
                "ok": False,
                "path": rel_path,
                "notes": ["missing report"],
            }
            continue
        try:
            data = _load_json_object(path)
            ok = bool(data.get("ok", False))
            if not ok:
                failed += 1
            _merge_forbidden_flags(forbidden, data)
            reports[name] = {
                "present": True,
                "ok": ok,
                "path": rel_path,
                "notes": _notes_for(name, data),
            }
        except Exception as exc:
            failed += 1
            reports[name] = {
                "present": True,
                "ok": False,
                "path": rel_path,
                "notes": [f"invalid report: {exc}"],
            }

    forbidden_detected = any(forbidden.values())
    if forbidden_detected:
        failed += 1
    report = {
        "schema": "nollm.dream_triage.v1",
        "status": "experimental_internal_only",
        "ok": missing == 0 and failed == 0,
        "summary": {
            "report_count": len(TRIAGE_REPORTS),
            "missing_report_count": missing,
            "failed_report_count": failed,
            "forbidden_semantics_detected": forbidden_detected,
        },
        "reports": reports,
        "forbidden_semantics": forbidden,
        "warnings": list(TRIAGE_WARNINGS),
    }
    validate_dream_triage_report(report)
    return report


def render_dream_triage_markdown(report: Mapping[str, object]) -> str:
    validate_dream_triage_report(report)
    status = "OK" if report["ok"] else "FAIL"
    summary = _mapping(report["summary"])
    reports = _mapping(report["reports"])
    forbidden = _mapping(report["forbidden_semantics"])
    lines = [
        "# Nollm Dream Geometry Failure Triage",
        "",
        f"Status: {status}",
        "",
        "## Summary",
        "",
        f"- Reports checked: {summary['report_count']}",
        f"- Missing reports: {summary['missing_report_count']}",
        f"- Failed reports: {summary['failed_report_count']}",
        f"- Forbidden semantics detected: {str(summary['forbidden_semantics_detected']).lower()}",
        "",
        "## Components",
        "",
        "| Component | Present | OK | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for name in sorted(reports):
        item = _mapping(reports[name])
        notes = "; ".join(str(note) for note in item.get("notes", []))
        lines.append(
            f"| {name} | {str(item['present']).lower()} | {str(item['ok']).lower()} | {notes} |"
        )
    lines.extend(
        [
            "",
            "## Forbidden Semantics",
            "",
            "| Flag | Detected |",
            "| --- | --- |",
        ]
    )
    for flag in FORBIDDEN_FLAGS:
        lines.append(f"| {flag} | {str(bool(forbidden.get(flag, False))).lower()} |")
    lines.extend(["", "## Warnings", ""])
    for warning in report["warnings"]:
        lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)


def validate_dream_triage_report(report: Mapping[str, object]) -> None:
    if not isinstance(report, Mapping):
        raise ValueError("triage report must be a mapping")
    for key in ("schema", "status", "ok", "summary", "reports", "forbidden_semantics", "warnings"):
        if key not in report:
            raise ValueError(f"missing triage report field: {key}")
    if report["schema"] != "nollm.dream_triage.v1":
        raise ValueError("unsupported triage schema")
    if report["status"] != "experimental_internal_only":
        raise ValueError("triage status must be experimental_internal_only")
    if not _is_json_primitive(report):
        raise ValueError("triage report must be JSON-primitive serializable")


def write_dream_triage_report(report: Mapping[str, object], output_path: Path | str) -> None:
    markdown = render_dream_triage_markdown(report)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8", newline="\n")


def write_dream_triage_json(report: Mapping[str, object], output_path: Path | str) -> None:
    validate_dream_triage_report(report)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _notes_for(name: str, data: Mapping[str, object]) -> list[str]:
    if name == "local_gate":
        pytest_info = _mapping(_mapping(data.get("components", {})).get("pytest", {}))
        return [f"pytest included: {str(bool(pytest_info.get('included', False))).lower()}"]
    if name == "golden_regression":
        return [f"failed_report_count: {data.get('failed_report_count', 0)}"]
    if name == "all_dream_checks_manifest":
        return [f"required_reports: {len(data.get('required_reports', []))}"]
    if name == "real_corpus_dry_run":
        return [f"shard_count: {data.get('shard_count', 0)}"]
    if name == "dream_suite":
        components = _mapping(data.get("components", {}))
        return [f"components: {len(components)}"]
    return []


def _load_json_object(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("report must be a JSON object")
    if not _is_json_primitive(data):
        raise ValueError("report must contain only JSON-primitive values")
    return data


def _merge_forbidden_flags(target: dict[str, bool], data: Mapping[str, object]) -> None:
    flags = data.get("forbidden_semantics")
    if not isinstance(flags, Mapping):
        return
    for flag in FORBIDDEN_FLAGS:
        target[flag] = bool(target[flag] or flags.get(flag, False))


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _is_json_primitive(value: object) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_primitive(item) for item in value)
    if isinstance(value, Mapping):
        return all(isinstance(key, str) and _is_json_primitive(item) for key, item in value.items())
    return False


__all__ = [
    "TRIAGE_REPORTS",
    "FORBIDDEN_FLAGS",
    "build_dream_triage_report",
    "render_dream_triage_markdown",
    "validate_dream_triage_report",
    "write_dream_triage_report",
    "write_dream_triage_json",
]
