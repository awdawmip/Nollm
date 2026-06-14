from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "reference" / "python" / "run_tests.py"
HARNESS = ROOT / "reference" / "python" / "tests" / "subprocess_harness.py"


def test_canonical_runner_uses_robust_process_management() -> None:
    runner_text = RUNNER.read_text(encoding="utf-8")
    harness_text = HARNESS.read_text(encoding="utf-8")

    assert "GROUP_TIMEOUT_SECONDS" in runner_text
    assert 'env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"' in runner_text
    assert "from subprocess_harness import run_subprocess" in runner_text
    assert "subprocess.run" not in runner_text
    assert "subprocess.Popen" in harness_text
    assert "subprocess.run" not in harness_text
    assert "start_new_session=os.name != \"nt\"" in harness_text
    assert "subprocess.CREATE_NEW_PROCESS_GROUP" in harness_text
    assert "os.killpg" in harness_text
    assert "process.kill()" in harness_text
    assert "tempfile.TemporaryDirectory" in harness_text
    assert "stdout_path" in harness_text
    assert "stderr_path" in harness_text
    assert "time.monotonic()" in harness_text


def test_tests_do_not_use_bare_subprocess_run() -> None:
    offenders = []
    forbidden = "subprocess." + "run("
    for path in sorted((ROOT / "reference" / "python" / "tests").glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        if forbidden in text:
            offenders.append(path.name)

    assert offenders == []
