from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/geometry/run_live_evidence_freeze_validation.py"


def _module():
    spec = importlib.util.spec_from_file_location("live_evidence_freeze_validation", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_evidence_freeze_reports_exact_line_size_and_sha() -> None:
    with TemporaryDirectory(prefix="nollm-evidence-freeze-") as raw_root:
        root = Path(raw_root)
        evidence = root / "evidence.jsonl"
        summary = root / "summary.json"
        payload = (
            json.dumps({"status": "completed", "stage": "recall", "resolved_provider": "host", "resolved_model_ref": "host/model"}, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        evidence.write_bytes(payload)

        result = _module().validate(evidence, summary)

        assert result["passed"]
        assert result["evidence"]["line_count"] == 1
        assert result["evidence"]["size_bytes"] == len(payload)
        assert summary.read_text(encoding="utf-8").endswith("\n")


def test_evidence_freeze_rejects_malformed_line() -> None:
    with TemporaryDirectory(prefix="nollm-evidence-freeze-") as raw_root:
        root = Path(raw_root)
        evidence = root / "evidence.jsonl"
        evidence.write_bytes(b"{}\nnot-json\n")
        try:
            _module().validate(evidence, root / "summary.json")
        except ValueError as error:
            assert "line 2" in str(error)
        else:
            raise AssertionError("malformed Evidence was accepted")
