from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys


def test_dg7_09_write_containment_excludes_caller_cwd_and_forbidden_work_dirs(tmp_path) -> None:
    caller = tmp_path / "caller"
    caller.mkdir()
    output = tmp_path / "receipt.json"
    work = tmp_path / "work"
    before_caller = _tree_manifest(caller)

    result = subprocess.run(
        [
            sys.executable,
            str(Path.cwd() / "reference/python/scripts/run_dg7_reference_runtime.py"),
            "--scenario",
            "fixed-dg7-v1",
            "--work-root",
            str(work),
            "--output",
            str(output),
        ],
        cwd=caller,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert _tree_manifest(caller) == before_caller
    for forbidden in ("field", "assembly", "recall", "cache", "database", "global-field"):
        assert not (work / forbidden).exists()
    assert output.exists()


def test_dg7_10_canonical_output_omits_paths_tracebacks_and_runtime_noise(tmp_path) -> None:
    output = tmp_path / "receipt.json"
    result = _run_cli(["--scenario", "fixed-dg7-v1", "--work-root", str(tmp_path / "work"), "--output", str(output)])
    rendered = output.read_text(encoding="utf-8")

    assert result.returncode == 0
    assert str(tmp_path) not in rendered
    assert "\\" not in rendered
    for forbidden in ("Traceback", "AttributeError", "KeyError", "TypeError", "ValueError", "runtime_handle", "cache_key", "semantic_score", "trust", "truth"):
        assert forbidden not in rendered


def test_dg7_11_unknown_scenario_missing_output_and_foreign_work_root_are_structured(tmp_path) -> None:
    unknown = _run_cli(["--scenario", "unknown", "--work-root", str(tmp_path / "unknown"), "--output", str(tmp_path / "unknown.json")])
    missing = _run_cli(["--scenario", "fixed-dg7-v1", "--work-root", str(tmp_path / "missing")])
    foreign_root = tmp_path / "foreign"
    foreign_root.mkdir()
    (foreign_root / "foreign.txt").write_text("do not touch", encoding="utf-8")
    foreign = _run_cli(["--scenario", "fixed-dg7-v1", "--work-root", str(foreign_root), "--output", str(tmp_path / "foreign.json")])

    for result, code in ((unknown, "DG7_INVALID_SCENARIO"), (missing, "DG7_INVALID_SCENARIO"), (foreign, "DG7_INVALID_WORK_ROOT")):
        assert result.returncode == 2
        payload = json.loads(result.stdout)
        assert payload["ok"] is False
        assert payload["kind"] == "nollm_dg7_reference_runtime_error"
        assert payload["reason_code"] == code
        assert "Traceback" not in result.stdout + result.stderr
    assert (foreign_root / "foreign.txt").read_text(encoding="utf-8") == "do not touch"
    assert not (tmp_path / "foreign.json").exists()


def test_dg7_13_invalid_explicit_set_is_structured_without_traceback(tmp_path) -> None:
    from nollm.dream_geometry.assembly import FiniteAdmissionSet, assemble_field_snapshot
    from nollm.dream_geometry.assembly.errors import DF1AssemblyError
    from nollm.dream_geometry.validation.dg7.runner import DG7RuntimeVerificationError, error_mapping

    try:
        assemble_field_snapshot(FiniteAdmissionSet("dg7_invalid_empty_set", ()))
    except DF1AssemblyError as exc:
        error = DG7RuntimeVerificationError("DG7_ASSEMBLY_REJECTED", getattr(exc, "reason_code", "DF1_REJECTED"))
    else:
        raise AssertionError("invalid explicit set unexpectedly assembled")

    payload = json.dumps(error_mapping(error.reason_code, str(error)), sort_keys=True)
    assert "DG7_ASSEMBLY_REJECTED" in payload
    assert "Traceback" not in payload


def test_dg7_c1_04_c_absence_only_accepts_filenotfound() -> None:
    from nollm.dream_geometry.validation.dg7.runner import DG7RuntimeVerificationError, _assert_admission_absent, error_mapping

    _assert_admission_absent(_AdmissionLookup(FileNotFoundError("adm_dg7_c")), "adm_dg7_c")

    for exc in (RuntimeError("store unavailable"), ValueError("bad payload")):
        with pytest_raises_dg7_admission_rejected() as captured:
            _assert_admission_absent(_AdmissionLookup(exc), "adm_dg7_c")
        payload = json.dumps(error_mapping(captured.reason_code, str(captured)), sort_keys=True)
        assert "DG7_ADMISSION_REJECTED" in payload
        assert not any(token in payload for token in ("Traceback", "RuntimeError", "ValueError", "nollm.dream_geometry"))


def test_dg5_dg6_dg7_are_classified_in_component_progress_not_as_runtime() -> None:
    roadmap = Path("ROADMAP.md").read_text(encoding="utf-8")
    progress = Path("docs/project/NOLLM_COMPONENT_PROGRESS_TABLE_V2_2.md").read_text(encoding="utf-8")
    delivery = Path("docs/delivery/DG7_DELIVERY_RECEIPT.md").read_text(encoding="utf-8")

    assert "DG5" in progress
    assert "Evidence-preserving trace compaction" in progress
    assert "does not replace original evidence or facts" in progress
    assert "DG6" in progress
    assert "Isolated verification-only snapshot-compaction projection" in progress
    assert "does not enter core recall or fact path" in progress
    assert "DG7" in progress
    assert "Explicit reference-runtime positive verification" in progress
    assert "not production runtime, daemon, network service, or terminal integration" in progress
    assert "production runtime" not in roadmap.lower()
    assert "core recall" not in roadmap.lower()
    assert "DG5: Evidence-preserving trace compaction capability is implemented as a finite, view-only CompressionPlan / CompactedTraceView with lossless expansion; final acceptance pending." not in roadmap
    assert "DG6 implemented; final acceptance pending." not in roadmap
    assert "main = origin/main = `47eca074045cede79d19b897ff4cae48dca23ab6` after fast-forward" in delivery
    assert "It does not implement production runtime integration, OpenClaw" in delivery
    assert "automatic memory" not in delivery
    assert "performance optimization" not in delivery


def test_dg7_14_runner_and_validation_package_exclude_forbidden_imports() -> None:
    roots = [Path("reference/python/nollm/dream_geometry/validation/dg7"), Path("reference/python/scripts/run_dg7_reference_runtime.py")]
    forbidden = ("integrations.openclaw", "requests", "urllib", "socket", "subprocess", "openclaw", "legacy", "memory_core")
    imports: list[tuple[Path, str]] = []
    for root in roots:
        paths = [root] if root.is_file() else sorted(root.glob("*.py"))
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend((path, alias.name) for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append((path, node.module))
    lowered = "\n".join(name.lower() for _path, name in imports)
    for token in forbidden:
        assert token not in lowered, (token, imports)


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "reference/python/scripts/run_dg7_reference_runtime.py", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )


def _tree_manifest(root: Path) -> tuple[str, ...]:
    return tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*")))


class pytest_raises_dg7_admission_rejected:
    def __enter__(self):
        from nollm.dream_geometry.validation.dg7.runner import DG7RuntimeVerificationError

        self._error_type = DG7RuntimeVerificationError
        return self

    def __exit__(self, exc_type, exc, traceback):
        assert exc_type is self._error_type
        assert exc.reason_code == "DG7_ADMISSION_REJECTED"
        self.reason_code = exc.reason_code
        self.message = str(exc)
        return True

    def __str__(self) -> str:
        return self.message


class _AdmissionLookup:
    def __init__(self, exc: Exception):
        self.exc = exc

    def get_admission_record(self, _admission_id: str):
        raise self.exc
