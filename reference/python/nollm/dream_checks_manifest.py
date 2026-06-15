from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

REQUIRED_REPORTS = (
    "examples/openclaw_dream/dream_suite_report.json",
    "examples/openclaw_dream/real_corpus_dry_run_report.json",
)

OPTIONAL_REPORTS = (
    "examples/openclaw_dream/dream_run_report.json",
    "examples/openclaw_dream/batch_report.json",
    "examples/openclaw_dream/regression_report.json",
)

FORBIDDEN_FLAG_KEYS = (
    "parent_child",
    "anchor_ownership",
    "folder_tree",
    "confirmed_placement",
)


def build_all_dream_checks_manifest(repo_root: Path | str) -> dict[str, object]:
    root = Path(repo_root)
    components: dict[str, object] = {}
    warnings: list[str] = [
        "E6 is internal experiment/regression infrastructure",
        "E6 is not a stable V1 recall/tool surface",
    ]
    forbidden_semantics = {key: False for key in FORBIDDEN_FLAG_KEYS}

    suite = _load_required(root, REQUIRED_REPORTS[0], warnings)
    corpus = _load_required(root, REQUIRED_REPORTS[1], warnings)

    if suite is not None:
        components["dream_suite"] = _suite_component(REQUIRED_REPORTS[0], suite)
        _merge_forbidden_flags(forbidden_semantics, suite)
    else:
        components["dream_suite"] = _missing_component(REQUIRED_REPORTS[0])

    if corpus is not None:
        components["real_corpus_dry_run"] = _corpus_component(REQUIRED_REPORTS[1], corpus)
        _merge_forbidden_flags(forbidden_semantics, corpus)
    else:
        components["real_corpus_dry_run"] = _missing_component(REQUIRED_REPORTS[1])

    optional = []
    for rel_path in OPTIONAL_REPORTS:
        report = _load_optional(root, rel_path, warnings)
        if report is not None:
            optional.append(rel_path)
            _merge_forbidden_flags(forbidden_semantics, report)

    failed_flags = [key for key, value in forbidden_semantics.items() if value]
    for key in failed_flags:
        warnings.append(f"forbidden semantic flag set: {key}")

    ok = (
        all(_component_ok(component) for component in components.values())
        and not failed_flags
    )
    manifest = {
        "schema": "nollm.dream_checks_manifest.v1",
        "ok": ok,
        "status": "experimental_internal_only",
        "components": components,
        "forbidden_semantics": forbidden_semantics,
        "required_reports": list(REQUIRED_REPORTS),
        "optional_reports": optional,
        "warnings": warnings,
    }
    validate_all_dream_checks_manifest(manifest)
    return manifest


def validate_all_dream_checks_manifest(manifest: Mapping[str, object]) -> None:
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be a mapping")
    for key in (
        "schema",
        "ok",
        "status",
        "components",
        "forbidden_semantics",
        "required_reports",
        "warnings",
    ):
        if key not in manifest:
            raise ValueError(f"missing manifest field: {key}")
    if manifest["schema"] != "nollm.dream_checks_manifest.v1":
        raise ValueError("unsupported manifest schema")
    if manifest["status"] != "experimental_internal_only":
        raise ValueError("manifest status must be experimental_internal_only")
    if not _is_json_primitive(manifest):
        raise ValueError("manifest must be JSON-primitive serializable")


def write_all_dream_checks_manifest(manifest: Mapping[str, object], output_path: Path | str) -> None:
    validate_all_dream_checks_manifest(manifest)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _load_required(root: Path, rel_path: str, warnings: list[str]) -> dict[str, object] | None:
    path = root / rel_path
    if not path.exists():
        warnings.append(f"missing required report: {rel_path}")
        return None
    try:
        return _load_json_object(path)
    except Exception as exc:
        warnings.append(f"invalid required report {rel_path}: {exc}")
        return None


def _load_optional(root: Path, rel_path: str, warnings: list[str]) -> dict[str, object] | None:
    path = root / rel_path
    if not path.exists():
        return None
    try:
        return _load_json_object(path)
    except Exception as exc:
        warnings.append(f"invalid optional report {rel_path}: {exc}")
        return None


def _load_json_object(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("report must be a JSON object")
    if not _is_json_primitive(data):
        raise ValueError("report must contain only JSON-primitive values")
    return data


def _suite_component(path: str, report: Mapping[str, object]) -> dict[str, object]:
    components = _mapping(report.get("components"))
    batch = _mapping(components.get("batch"))
    regression = _mapping(components.get("regression"))
    return {
        "ok": bool(report.get("ok")),
        "path": path,
        "summary": {
            "component_count": len(components),
            "failed_invariant_count": int(batch.get("failed_invariant_count", 0)),
            "failed_case_count": int(regression.get("failed_case_count", 0)),
        },
    }


def _corpus_component(path: str, report: Mapping[str, object]) -> dict[str, object]:
    return {
        "ok": bool(report.get("ok")) and int(report.get("failed_invariant_count", 0)) == 0,
        "path": path,
        "summary": {
            "file_count": int(report.get("file_count", 0)),
            "shard_count": int(report.get("shard_count", 0)),
            "placement_count": int(report.get("placement_count", 0)),
            "failed_invariant_count": int(report.get("failed_invariant_count", 0)),
        },
    }


def _missing_component(path: str) -> dict[str, object]:
    return {
        "ok": False,
        "path": path,
        "summary": {},
    }


def _component_ok(component: object) -> bool:
    return isinstance(component, Mapping) and bool(component.get("ok"))


def _merge_forbidden_flags(target: dict[str, bool], report: Mapping[str, object]) -> None:
    flags = report.get("forbidden_semantics")
    if not isinstance(flags, Mapping):
        return
    for key in FORBIDDEN_FLAG_KEYS:
        target[key] = bool(target[key] or flags.get(key, False))


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
    "REQUIRED_REPORTS",
    "OPTIONAL_REPORTS",
    "FORBIDDEN_FLAG_KEYS",
    "build_all_dream_checks_manifest",
    "validate_all_dream_checks_manifest",
    "write_all_dream_checks_manifest",
]
