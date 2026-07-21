from importlib.util import module_from_spec, spec_from_file_location
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/evidence/verify_atomic_growth_evidence.py"


def load_module():
    spec = spec_from_file_location("atomic_growth_evidence", SCRIPT)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_records_reports_in_progress_relation_counterexample(tmp_path):
    module = load_module()
    events = []
    for index in range(9):
        statement_id = f"dream:{index}"
        events.append({
            "stage": "absorption_batch",
            "capture_ids": [f"capture-{index}"],
            "statement_count": 1,
            "writer_resolved": {"resolved_model_ref": "provider/model"},
            "cartographer_resolved": [{"resolved_model_ref": "provider/model"}],
            "validated_plans": [{
                "statement": {"statement_id": statement_id},
                "lenses": [{"unresolved": index != 1}],
                "relation_groups": [[[0, 0]]] if index == 1 else [],
            }],
            "durable_outcomes": [{
                "statement_id": statement_id,
                "action": "new_local" if index == 1 else "independent_seed",
                "placement_mode": "related_growth" if index == 1 else "independent_seed",
                "durable_commit": {
                    "commit_state": "reopen_verified",
                    "reopen_verified": True,
                    "handle": {"geometry_address": {"profile_id": "p", "chart_id": "c", "layer": 0, "q": index, "r": 0, "phase": None}},
                },
            }],
        })
    for index in range(5):
        events.append({
            "stage": "fast_recall",
            "status": "completed",
            "request_id": f"recall-{index}",
            "selected_entry": {"profile_id": "p", "chart_id": "c", "layer": 0, "q": 4, "r": 0, "phase": None},
            "statement_ids": ["dream:4"],
            "selected_paths": [{"statement_id": "dream:4", "path": []}],
            "hidden_provider_calls": 1,
            "resolved_model_ref": "provider/model",
        })
    events.append({"stage": "fast_recall", "status": "complete_none", "request_id": "recall-none", "statement_ids": [], "hidden_provider_calls": 1})
    evidence = tmp_path / "evidence.jsonl"
    evidence.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
    payload = evidence.read_bytes()
    freeze = tmp_path / "evidence.jsonl.freeze.json"
    freeze.write_text(json.dumps({
        "sha256": sha256(payload).hexdigest(),
        "bytes": len(payload),
        "source_stability": {"stable": True},
        "gateway_probe_before": {"listeners": [], "gateway_processes": []},
        "gateway_probe_after": {"listeners": [], "gateway_processes": []},
        "plugin_config": {"active_writer_paths": []},
    }), encoding="utf-8")
    capture_state = tmp_path / "capture_state"
    captures = capture_state / "captures"
    events_root = capture_state / "events"
    captures.mkdir(parents=True)
    events_root.mkdir(parents=True)
    for index in range(9):
        (captures / f"capture-{index}.json").write_text(json.dumps({
            "schema_version": "nollm_openclaw_durable_capture_v1",
            "capture_id": f"capture-{index}",
        }), encoding="utf-8")
        event_dir = events_root / f"capture-{index}"
        event_dir.mkdir()
        (event_dir / "admitted.json").write_text(json.dumps({
            "schema_version": "nollm_openclaw_capture_state_event_v1",
            "capture_id": f"capture-{index}",
            "status": "admitted",
            "attempt": 2 if index == 1 else 1,
        }), encoding="utf-8")
    (events_root / "capture-1" / "retry.json").write_text(json.dumps({
        "schema_version": "nollm_openclaw_capture_state_event_v1",
        "capture_id": "capture-1",
        "status": "retry",
        "attempt": 1,
        "batch_id": "batch-1",
        "error": "structured model output failed",
    }), encoding="utf-8")

    records, summary = module.build_records(evidence, freeze, capture_state)
    assert summary["growth"]["capture_count"] == 9
    assert summary["growth"]["related_growth_count"] == 1
    assert summary["growth"]["retry_event_count"] == 1
    assert summary["recall"]["t0_recall_count"] == 0
    assert summary["recall"]["nonempty_path_count"] == 0
    assert summary["gate_d"]["passed"] is False
    assert records[-1]["record_type"] == "summary"
