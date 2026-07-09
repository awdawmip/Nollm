from __future__ import annotations

import json
import subprocess
import sys

from nollm.grf.capture import GRFCaptureRequest
from nollm.grf.coverage_template import LATERAL
from nollm.grf.facade import GRFFacade
from nollm.grf.json_canonical import canonical_dumps
from nollm.grf.recall import QueryProbe, RecallBudget


def test_facade_replay_matches_recall(tmp_path) -> None:
    facade = GRFFacade(tmp_path)
    receipt = facade.capture(GRFCaptureRequest("capture:facade:replay", "replay content", "validation_fixture", ("source:facade:replay",), "2026-07-09T00:00:00Z"))
    facade.admit(receipt.shard_id, "source:facade:replay", {"policy_id": "validation_fixture_policy", "chart_id": "chart_facade"}, "2026-07-09T00:00:01Z")
    query = QueryProbe("query:facade:replay", "shard_id", receipt.shard_id, (LATERAL,), RecallBudget(0, 1, 0, 1, 0, 1))

    assert facade.replay_recall(query).to_mapping() == facade.recall(query).to_mapping()


def test_cli_emits_single_json_object_and_stable_errors(tmp_path) -> None:
    script = _script()
    request = tmp_path / "capture.json"
    request.write_bytes(
        canonical_dumps(
            {
                "kind": "nollm_grf_capture_request",
                "version": "1",
                "capture_id": "capture:cli:1",
                "content": "cli content",
                "origin_kind": "validation_fixture",
                "source_window_refs": ("source:cli:1",),
                "recorded_at": "2026-07-09T00:00:00Z",
            }
        )
    )
    completed = subprocess.run([sys.executable, str(script), "capture", "--workspace", str(tmp_path / "workspace"), "--request", str(request)], text=True, capture_output=True, timeout=20)
    lines = completed.stdout.splitlines()
    assert completed.returncode == 0
    assert len(lines) == 1
    assert json.loads(lines[0])["ok"] is True

    bad = subprocess.run([sys.executable, str(script), "capture", "--workspace", str(tmp_path / "workspace"), "--request", str(tmp_path / "missing.json")], text=True, capture_output=True, timeout=20)
    payload = json.loads(bad.stdout)
    assert bad.returncode == 2
    assert payload == {"ok": False, "error": {"code": "FileNotFoundError", "message": "request failed"}}
    assert str(tmp_path) not in bad.stdout


def _script():
    return __import__("pathlib").Path(__file__).resolve().parents[2] / "scripts" / "run_nollm_grf.py"
