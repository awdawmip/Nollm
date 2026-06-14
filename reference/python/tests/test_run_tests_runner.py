from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "reference" / "python" / "run_tests.py"


def test_canonical_runner_uses_robust_process_management() -> None:
    text = RUNNER.read_text(encoding="utf-8")

    assert "GROUP_TIMEOUT_SECONDS" in text
    assert 'env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"' in text
    assert "subprocess.Popen" in text
    assert "subprocess.run" not in text
    assert "start_new_session=os.name != \"nt\"" in text
    assert "subprocess.CREATE_NEW_PROCESS_GROUP" in text
    assert "os.killpg" in text
    assert "process.kill()" in text
    assert "tempfile.TemporaryDirectory" in text
    assert "stdout_path" in text
    assert "stderr_path" in text
    assert "time.monotonic()" in text
