from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/evidence/freeze_live_evidence.py"


def load_module():
    spec = spec_from_file_location("runtime_evidence_freeze", SCRIPT)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_freeze_requires_writer_rotation_and_preserves_exact_bytes(tmp_path, monkeypatch):
    module = load_module()
    live = tmp_path / "validation" / "live" / "run-one" / "events.jsonl"
    frozen = tmp_path / "validation" / "frozen" / "task" / "evidence.jsonl"
    config = tmp_path / "openclaw.json"
    live.parent.mkdir(parents=True)
    payload = b'{"event_type":"one"}\n{"event_type":"two"}\n'
    live.write_bytes(payload)
    config.write_text(json.dumps({"plugins": {"nollm": {"debug_trace": True, "evidence_path": str(live)}}}), encoding="utf-8")
    monkeypatch.setattr(module, "windows_gateway_probe", lambda port: {"backend": "test", "port": port, "listeners": [], "gateway_processes": []})

    with pytest.raises(RuntimeError, match="rotated or disabled"):
        module.freeze_evidence(live, frozen, config, stability_seconds=0)

    next_live = tmp_path / "validation" / "live" / "run-two" / "events.jsonl"
    config.write_text(json.dumps({"plugins": {"nollm": {"debug_trace": True, "evidence_path": str(next_live)}}}), encoding="utf-8")
    metadata = module.freeze_evidence(live, frozen, config, stability_seconds=0)
    assert frozen.read_bytes() == payload
    assert metadata["sha256"] == __import__("hashlib").sha256(payload).hexdigest()
    assert metadata["line_count"] == 2
    assert metadata["plugin_config"]["source_writer_active_at_freeze"] is False
    assert metadata["operator_attestation"] is None


def test_frozen_target_can_never_be_active_writer(tmp_path, monkeypatch):
    module = load_module()
    live = tmp_path / "live" / "run" / "events.jsonl"
    frozen = tmp_path / "frozen" / "task" / "evidence.jsonl"
    config = tmp_path / "openclaw.json"
    live.parent.mkdir(parents=True)
    live.write_text("{}\n", encoding="utf-8")
    config.write_text(json.dumps({"debug_trace": True, "evidence_path": str(frozen)}), encoding="utf-8")
    monkeypatch.setattr(module, "windows_gateway_probe", lambda port: {})
    with pytest.raises(RuntimeError, match="configured as a writer"):
        module.freeze_evidence(live, frozen, config, stability_seconds=0)


def test_gateway_process_detection_excludes_freeze_and_probe_commands():
    module = load_module()
    assert module._is_gateway_process({
        "Name": "node.exe",
        "CommandLine": '"C:\\Program Files\\nodejs\\node.exe" C:\\tools\\openclaw\\dist\\index.js gateway --port 18789',
    })
    assert not module._is_gateway_process({
        "Name": "python.exe",
        "CommandLine": "python freeze_live_evidence.py --plugin-config openclaw.json --gateway-port 18789",
    })
    assert not module._is_gateway_process({
        "Name": "pwsh.exe",
        "CommandLine": "pwsh -Command openclaw gateway status",
    })
    assert not module._is_gateway_process({
        "Name": "node.exe",
        "CommandLine": "node helper.js --gateway-port 18789 --plugin openclaw",
    })
