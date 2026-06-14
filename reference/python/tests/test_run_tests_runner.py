from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "reference" / "python" / "run_tests.py"
HARNESS = ROOT / "reference" / "python" / "tests" / "subprocess_harness.py"


def test_canonical_runner_delegates_to_full_pytest() -> None:
    runner_text = RUNNER.read_text(encoding="utf-8")

    assert "sys.dont_write_bytecode = True" in runner_text
    assert 'os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")' in runner_text
    assert "from pytest import main as pytest_main" in runner_text
    assert 'pytest_main(["-q"])' in runner_text
    assert "subprocess_harness" not in runner_text
    assert "GROUP_TIMEOUT_SECONDS" not in runner_text
    assert "subprocess.run" not in runner_text


def test_shared_subprocess_harness_remains_robust() -> None:
    harness_text = HARNESS.read_text(encoding="utf-8")

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
