from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
import sys


def test_dg7_07_two_fresh_process_receipts_are_identical(tmp_path) -> None:
    first = _run_cli(tmp_path / "one")
    second = _run_cli(tmp_path / "two")

    assert first == second
    assert sha256(first.encode("utf-8")).hexdigest() == "f78ec9feb031759c2ce0aca023b3f9e809049f4a7cb63cb180b301e2a407c724"
    for forbidden in (str(tmp_path), "\\", "Traceback", "AttributeError", "KeyError", "TypeError", "ValueError"):
        assert forbidden not in first


def test_dg7_08_owned_work_root_reopen_returns_same_receipt_without_extra_files(tmp_path) -> None:
    root = tmp_path / "owned"
    first = _run_cli(root)
    before = _tree_manifest(root / "work")
    second = _run_cli(root)
    after = _tree_manifest(root / "work")

    assert first == second
    assert before == after


def test_dg7_report_regeneration_matches_committed_report(tmp_path) -> None:
    output = tmp_path / "report.md"
    result = subprocess.run(
        [sys.executable, "validation/dg7/run_dg7_validation.py", "--output", str(output)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    committed = Path("docs/validation/DG7_REFERENCE_RUNTIME_POSITIVE_VERIFICATION_REPORT.md").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == committed


def _run_cli(root: Path) -> str:
    root.mkdir(parents=True, exist_ok=True)
    output = root / "receipt.json"
    result = subprocess.run(
        [
            sys.executable,
            "reference/python/scripts/run_dg7_reference_runtime.py",
            "--scenario",
            "fixed-dg7-v1",
            "--work-root",
            str(root / "work"),
            "--output",
            str(output),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return output.read_text(encoding="utf-8")


def _tree_manifest(root: Path) -> tuple[str, ...]:
    return tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()))
