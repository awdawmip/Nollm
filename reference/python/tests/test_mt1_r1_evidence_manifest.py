from __future__ import annotations


REQUIRED_VERIFICATION_KEYS = {
    "archive_verified",
    "coverage_ratio",
    "provenance_verified",
    "atomicity_failure_test_verified",
    "idempotence_verified",
    "source_unchanged",
    "scope_guard_ok",
    "full_test_suite_passed",
}


def validate_single_bundle_review_manifest(manifest: dict[str, object]) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema") != "nollm.mt1.single_bundle_evidence.v1":
        errors.append("schema")
    project = manifest.get("project")
    if not isinstance(project, dict) or not project.get("head_commit"):
        errors.append("project.head_commit")
    if manifest.get("input_classification") != "synthetic_non_sensitive":
        errors.append("input_classification")
    included = manifest.get("included_artifacts")
    if not isinstance(included, list) or not included:
        errors.append("included_artifacts")
    excluded = set(manifest.get("excluded_artifacts", [])) if isinstance(manifest.get("excluded_artifacts"), list) else set()
    for required in ["real user memory", "real OpenClaw workspace", "secrets", "tokens", "cache", "venv"]:
        if required not in excluded:
            errors.append(f"excluded:{required}")
    verification = manifest.get("verification")
    if not isinstance(verification, dict):
        errors.append("verification")
    else:
        missing = REQUIRED_VERIFICATION_KEYS - set(verification)
        errors.extend(f"verification:{key}" for key in sorted(missing))
        for key in REQUIRED_VERIFICATION_KEYS - {"coverage_ratio"}:
            if verification.get(key) is not True:
                errors.append(f"verification_not_true:{key}")
        if verification.get("coverage_ratio") != 1.0:
            errors.append("coverage_ratio")
    return errors


def test_t14_evidence_manifest_exact_schema_validation() -> None:
    manifest = {
        "schema": "nollm.mt1.single_bundle_evidence.v1",
        "created_at": "2026-06-21T00:00:00Z",
        "project": {
            "branch": "feature/nollm-memory-takeover-mt1-r1-integrity-atomicity",
            "base_commit": "9cfff6512274a1b346fb1bcc6511eb3f4a29b49b",
            "head_commit": "abc",
        },
        "evidence_ref": "evidence/mt1-r1-integrity-atomicity",
        "input_classification": "synthetic_non_sensitive",
        "included_artifacts": [{"path": "reports/coverage.json", "purpose": "coverage"}],
        "excluded_artifacts": ["real user memory", "real OpenClaw workspace", "secrets", "tokens", "cache", "venv"],
        "verification": {
            "archive_verified": True,
            "coverage_ratio": 1.0,
            "provenance_verified": True,
            "atomicity_failure_test_verified": True,
            "idempotence_verified": True,
            "source_unchanged": True,
            "scope_guard_ok": True,
            "full_test_suite_passed": True,
        },
    }

    assert validate_single_bundle_review_manifest(manifest) == []
