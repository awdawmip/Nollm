from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
import subprocess
import sys

import pytest

from nollm.dream_geometry.admission import placement_plan_payload
from nollm.dream_geometry.capture import CaptureStateStore
from nollm.dream_geometry.host_admission_gateway import admit_from_text
import nollm.dream_geometry.host_admission_gateway.gateway as hag_gateway
from nollm.dream_geometry.host_execution import HostPlanBindings, execute_host_plan

from test_hx1_trusted_host_bridge import (
    RECORDED_AT,
    _admission_record_exists,
    _admission_request,
    _candidate_id,
    _capture,
    _expected_shard,
    capture_only_fixture,
)


def test_hag1_01_canonical_single_member_explicit_admission_success(tmp_path) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))

    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is True
    assert envelope["action"] == "admit"
    assert envelope["result"]["host_execution"]["status"] == "completed"
    assert envelope["result"]["host_execution"]["completed_stages"] == ["admission"]
    assert envelope["result"]["admission_ids"] == ["adm_hx1_d"]
    assert envelope["result"]["members"][0]["shard_id"].startswith("shard:ci1:")
    assert envelope["result"]["members"][0]["cx2_projection"]["candidate_ref"].startswith("dac_")
    assert envelope["result"]["members"][0]["cx2_projection"]["shard_ref"].startswith("shard_")
    assert envelope["result"]["members"][0]["cx2_projection"]["shard_ref"] != envelope["result"]["members"][0]["shard_id"]
    assert _admission_record_exists(workspace, "adm_hx1_d")


def test_hag1_02_two_member_batch_preserves_member_identity_and_order(tmp_path) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d", "e"))

    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is True
    assert [item["admission_id"] for item in envelope["result"]["members"]] == ["adm_hx1_d", "adm_hx1_e"]
    assert [item["member_id"] for item in envelope["result"]["members"]] == ["bam_hag1_d", "bam_hag1_e"]
    assert all(item["shard_id"].startswith("shard:ci1:") for item in envelope["result"]["members"])
    assert _admission_record_exists(workspace, "adm_hx1_d")
    assert _admission_record_exists(workspace, "adm_hx1_e")


def test_hag1_03_second_member_invalid_keeps_batch_zero_write(tmp_path) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d", "e"))
    request["members"][1]["admission"]["growth_submission"]["subject_shard_id"] = "shard:ci1:wrong"

    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "HAG_ADMISSION_REJECTED"
    assert not _admission_record_exists(workspace, "adm_hx1_d")
    assert not _admission_record_exists(workspace, "adm_hx1_e")


def test_hag1_c1r_02_plan_binding_dual_namespace_is_explicit(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))
    seen = {}
    real_execute = hag_gateway.execute_host_plan

    def spy(plan, bindings, context):
        seen["plan"] = plan
        seen["bindings"] = bindings
        return real_execute(plan, bindings, context)

    monkeypatch.setattr(hag_gateway, "execute_host_plan", spy)
    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is True
    member = envelope["result"]["members"][0]
    projection = member["cx2_projection"]
    binding = seen["bindings"].admission_bindings[0]
    plan_decision = seen["plan"]["promotion_decisions"][0]
    plan_ref = seen["plan"]["admission_request_refs"][0]
    assert plan_decision["candidate_id"] == projection["candidate_ref"]
    assert plan_decision["shard_id"] == projection["shard_ref"]
    assert plan_ref["shard_id"] == projection["shard_ref"]
    assert binding.candidate_id == projection["candidate_ref"]
    assert binding.declared_shard_id == projection["shard_ref"]
    assert binding.actual_candidate_id == member["candidate_id"]
    assert binding.request.dream_shard.shard_id == member["shard_id"]
    assert binding.decision.candidate_id == member["candidate_id"]
    assert binding.decision.shard_id == member["shard_id"]


def test_hag1_c1r_03_legacy_public_shard_alias_rejects_before_evidence_read(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))
    request["window"]["member_shard_ids"] = ["shard_hag1_d"]
    request["members"][0]["promotion_decision"]["shard_id"] = "shard_hag1_d"
    request["members"][0]["admission"]["shard_id"] = "shard_hag1_d"
    calls = {"evidence": 0}

    def fail_open(*_args, **_kwargs):
        calls["evidence"] += 1
        raise AssertionError("evidence read should not be reached")

    monkeypatch.setattr(hag_gateway, "open_evidence_store", fail_open)
    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "HAG_ADMISSION_REJECTED"
    assert calls["evidence"] == 0
    assert not _admission_record_exists(workspace, "adm_hx1_d")


def test_hag1_c1r_04_candidate_declaration_mismatch_rejects_pre_evidence(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d", "e"))
    other = request["members"][1]["admission"]["shard_id"]
    request["window"]["member_shard_ids"] = [other]
    request["members"] = [request["members"][0]]
    request["members"][0]["promotion_decision"]["shard_id"] = other
    request["members"][0]["admission"]["shard_id"] = other

    def fail_open(*_args, **_kwargs):
        raise AssertionError("evidence read should not be reached")

    monkeypatch.setattr(hag_gateway, "open_evidence_store", fail_open)
    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "HAG_ADMISSION_REJECTED"
    assert not _admission_record_exists(workspace, "adm_hx1_d")


def test_hag1_c1r_05_evidence_identity_mismatch_rejects_without_content_leak(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))
    real_store = hag_gateway.open_evidence_store(workspace / "evidence")
    wrong_shard = replace(real_store.get_dream_shard(request["members"][0]["admission"]["shard_id"]), shard_id="shard:ci1:wrong")

    class EvidenceWrapper:
        def get_dream_shard(self, _shard_id):
            return wrong_shard

    monkeypatch.setattr(hag_gateway, "open_evidence_store", lambda _root: EvidenceWrapper())
    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "HAG_ADMISSION_REJECTED"
    assert "content" not in json.dumps(envelope)
    assert not _admission_record_exists(workspace, "adm_hx1_d")


def test_hag1_c1r_06_projection_determinism_no_mapping_and_collision_reject(tmp_path, monkeypatch) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))
    first = admit_from_text(workspace, json.dumps(request))
    second = admit_from_text(workspace, json.dumps(request))

    assert first["ok"] is True
    assert second["ok"] is True
    assert first["result"]["members"][0]["cx2_projection"] == second["result"]["members"][0]["cx2_projection"]
    names = [path.name.lower() for path in workspace.rglob("*")]
    assert not any("mapping" in name or "alias" in name or "projection_registry" in name for name in names)

    collision_workspace = tmp_path / "collision"
    collision_request = _request(collision_workspace, ("d", "e"))
    monkeypatch.setattr(hag_gateway, "_projection_for", lambda *_args: {"candidate_ref": "dac_collision", "shard_ref": "shard_collision"})
    envelope = admit_from_text(collision_workspace, json.dumps(collision_request))
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "HAG_ADMISSION_REJECTED"


def test_hag1_c1r_07_two_real_members_preserve_public_order_and_projection_uniqueness(tmp_path) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("e", "d"))

    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is True
    assert [item["member_id"] for item in envelope["result"]["members"]] == ["bam_hag1_e", "bam_hag1_d"]
    assert len({item["cx2_projection"]["candidate_ref"] for item in envelope["result"]["members"]}) == 2
    assert len({item["cx2_projection"]["shard_ref"] for item in envelope["result"]["members"]}) == 2
    assert all(item["shard_id"].startswith("shard:ci1:") for item in envelope["result"]["members"])
    assert all(not item["shard_id"].startswith("shard_hag1") for item in envelope["result"]["members"])


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r["window"].__setitem__("closed_at", RECORDED_AT),
        lambda r: r["window"].__setitem__("opened_at", "2025-01-01T00:00:00+00:00"),
        lambda r: r["window"].__setitem__("source_window_refs", ["source:hag1:test", "source:hag1:second"]),
    ],
)
def test_hag1_c1r_window_semantics_reject_pre_io(tmp_path, monkeypatch, mutate) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))
    sentinel = workspace / "capture" / "hag1_window_sentinel.txt"
    sentinel.write_text("sentinel", encoding="utf-8")
    mutate(request)

    def fail_candidate(*_args, **_kwargs):
        raise AssertionError("candidate state should not be reached")

    monkeypatch.setattr(hag_gateway, "CaptureStateStore", fail_candidate)
    monkeypatch.setattr(hag_gateway, "open_evidence_store", lambda *_args: (_ for _ in ()).throw(AssertionError("evidence should not be reached")))
    monkeypatch.setattr(hag_gateway, "execute_host_plan", lambda *_args: (_ for _ in ()).throw(AssertionError("HX1 should not be reached")))
    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "HAG_INVALID_REQUEST"
    assert sentinel.read_text(encoding="utf-8") == "sentinel"
    assert not _admission_record_exists(workspace, "adm_hx1_d")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r["members"][0].__setitem__("candidate_id", "dac:unknown"),
        lambda r: r["members"][0]["promotion_decision"].__setitem__("shard_id", "shard:ci1:wrong"),
        lambda r: r["members"][0]["admission"].__setitem__("shard_id", "shard:ci1:wrong"),
    ],
)
def test_hag1_04_candidate_and_shard_mismatches_reject(tmp_path, mutate) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))
    mutate(request)

    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is False
    assert envelope["error"]["code"] in {"HAG_INVALID_REQUEST", "HAG_ADMISSION_REJECTED"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("decision", "defer"),
        ("decision", "do_not_admit"),
        ("decided_by", "cortex_suggestion"),
        ("next_action", "auto_admit"),
    ],
)
def test_hag1_05_non_promote_cortex_or_wrong_next_action_reject_pre_io(tmp_path, field, value) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))
    request["members"][0]["promotion_decision"][field] = value

    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "HAG_INVALID_REQUEST"
    assert not _admission_record_exists(workspace, "adm_hx1_d")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r["members"].append(deepcopy(r["members"][0])),
        lambda r: r["members"][1].__setitem__("candidate_id", r["members"][0]["candidate_id"]),
        lambda r: r["members"][1]["admission"].__setitem__("shard_id", r["members"][0]["admission"]["shard_id"]),
        lambda r: r["members"][1]["promotion_decision"].__setitem__("decision_id", r["members"][0]["promotion_decision"]["decision_id"]),
        lambda r: r["members"][1]["admission"].__setitem__("admission_id", r["members"][0]["admission"]["admission_id"]),
        lambda r: r["members"][1]["admission"]["placement_plan"].__setitem__("plan_id", r["members"][0]["admission"]["placement_plan"]["plan_id"]),
    ],
)
def test_hag1_06_duplicate_public_id_rejects(tmp_path, mutate) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d", "e"))
    mutate(request)

    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "HAG_INVALID_REQUEST"


@pytest.mark.parametrize(
    "payload",
    [
        "{",
        '{"kind":"nollm_hag_admission_request","kind":"x"}',
        '{"kind":"legacy"}',
    ],
)
def test_hag1_07_malformed_duplicate_key_and_legacy_reject(tmp_path, payload) -> None:
    workspace = tmp_path / "work"
    envelope = admit_from_text(workspace, payload)
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "HAG_INVALID_REQUEST"


@pytest.mark.parametrize("field", ["workspace", "file_path", "content", "embedding", "global_search", "auto_axis", "truth_score", "importance_score"])
def test_hag1_08_forbidden_raw_or_automation_fields_reject(tmp_path, field) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))
    request["members"][0]["admission"][field] = "blocked"

    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "HAG_INVALID_REQUEST"


@pytest.mark.parametrize("marker", [None, "not-json", '{"owner":"other","marker_version":"1"}'])
def test_hag1_09_non_hx1_owned_workspace_rejects_without_scaffold(tmp_path, marker) -> None:
    workspace = tmp_path / "unowned"
    workspace.mkdir()
    if marker is not None:
        (workspace / ".hx1_host_execution_root.json").write_text(marker, encoding="utf-8")
    request = _request_payload("d")

    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "HAG_WORKSPACE_NOT_OWNED"
    for name in ("capture", "evidence", "cortex", "admission"):
        assert not (workspace / name).exists()


def test_hag1_10_sentinel_files_survive_success_reopen_and_rejection(tmp_path) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))
    sentinel = workspace / "capture" / "hag1_sentinel.txt"
    sentinel.write_text("sentinel", encoding="utf-8")

    assert admit_from_text(workspace, json.dumps(request))["ok"] is True
    assert admit_from_text(workspace, json.dumps(request))["ok"] is True
    bad = deepcopy(request)
    bad["members"][0]["promotion_decision"]["decision"] = "defer"
    assert admit_from_text(workspace, json.dumps(bad))["ok"] is False
    assert sentinel.read_text(encoding="utf-8") == "sentinel"


def test_hag1_11_same_request_reopens_changed_payload_rejects_without_overwrite(tmp_path) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))

    first = admit_from_text(workspace, json.dumps(request))
    second = admit_from_text(workspace, json.dumps(request))
    changed = deepcopy(request)
    changed["members"][0]["admission"]["growth_submission"]["do_not_infer"] = ["changed payload"]
    third = admit_from_text(workspace, json.dumps(changed))

    assert first["ok"] is True
    assert second["ok"] is True
    assert third["ok"] is False
    assert third["error"]["code"] in {"HAG_REOPEN_MISMATCH", "HAG_ADMISSION_REJECTED"}
    assert _admission_record_exists(workspace, "adm_hx1_d")


def test_hag1_12_lower_layer_rejection_is_not_reported_as_success(tmp_path) -> None:
    workspace = tmp_path / "work"
    request = _request(workspace, ("d",))
    request["members"][0]["admission"]["placement_plan"]["axis_placements"] = request["members"][0]["admission"]["placement_plan"]["axis_placements"][:1]

    envelope = admit_from_text(workspace, json.dumps(request))

    assert envelope["ok"] is False
    assert envelope["error"]["code"] in {"HAG_INVALID_REQUEST", "HAG_ADMISSION_REJECTED"}
    assert "result" not in envelope


def test_hag1_13_source_guard_has_no_forbidden_runtime_or_discovery_imports() -> None:
    root = __import__("pathlib").Path("reference/python/nollm/dream_geometry/host_admission_gateway")
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    forbidden = ("import socket", "import requests", "import sqlite", "openclaw")
    assert not any(item in text.lower() for item in forbidden)
    assert "host_capture_gateway" not in text


def test_hag1_14_cli_stdout_single_envelope_and_no_traceback(tmp_path) -> None:
    request = tmp_path / "bad.json"
    request.write_text('{"kind":"legacy"}', encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            "reference/python/scripts/run_nollm_host_admission_gateway.py",
            "admit",
            "--workspace",
            str(tmp_path / "missing"),
            "--request",
            str(request),
        ],
        cwd=__import__("pathlib").Path.cwd(),
        text=True,
        capture_output=True,
        timeout=15,
    )
    payload = json.loads(proc.stdout)
    assert proc.returncode != 0
    assert payload["ok"] is False
    assert proc.stdout.count("\n") == 1
    assert "Traceback" not in proc.stderr
    assert str(tmp_path) not in proc.stdout


def test_hag1_15_hcg_hx_surfaces_remain_external_and_no_v1_cli_registration() -> None:
    gateway = __import__("pathlib").Path("reference/python/nollm/dream_geometry/host_admission_gateway/gateway.py").read_text(encoding="utf-8")
    cli = __import__("pathlib").Path("reference/python/nollm/cli.py").read_text(encoding="utf-8")
    assert "host_capture_gateway" not in gateway
    assert "run_nollm_host_admission_gateway" not in cli


def _request(workspace, labels: tuple[str, ...]) -> dict:
    for label in labels:
        plan, bindings, context = capture_only_fixture(workspace, label, plan_id=f"cx2_hag1_capture_{label}")
        execute_host_plan(plan, bindings, context)
    return _request_payload(*labels)


def _request_payload(*labels: str) -> dict:
    members = []
    shard_ids = []
    for label in labels:
        capture_request, policy = _capture(label)
        candidate_id = _candidate_id(capture_request, policy)
        shard_id = _actual_shard_id_for_request(label)
        admission = _admission_request(label, _expected_shard_for_request(label))
        shard_ids.append(shard_id)
        members.append(
            {
                "member_id": f"bam_hag1_{label}",
                "candidate_id": candidate_id,
                "promotion_decision": {
                    "decision_id": f"pmd_hag1_{label}",
                    "candidate_id": candidate_id,
                    "shard_id": shard_id,
                    "decision": "promote",
                    "reasons": ["explicit_pin", "manual_batch_selection"],
                    "decided_by": "human_operator",
                    "recorded_at": RECORDED_AT,
                    "next_action": "request_growth_submission",
                },
                "admission": {
                    "admission_id": f"adm_hx1_{label}",
                    "shard_id": shard_id,
                    "growth_submission": admission.growth_submission,
                    "placement_plan": placement_plan_payload(admission.placement_plan),
                    "recorded_at": RECORDED_AT,
                },
            }
        )
    return {
        "kind": "nollm_hag_admission_request",
        "version": "1",
        "request_id": "hag_req_" + "_".join(labels or ("empty",)),
        "submitted_at": RECORDED_AT,
        "window": {
            "window_id": "baw_hag1_" + "_".join(labels or ("empty",)),
            "member_shard_ids": shard_ids,
            "source_window_refs": ["source:hag1:test"],
            "opened_at": RECORDED_AT,
            "closed_at": None,
            "shared_policy_ref": "cp_hag1_manual",
            "shared_geometry_profile_ref": "da1_sealed_default_v1",
            "status": "ready_for_selection",
        },
        "members": members,
    }


def _expected_shard_for_request(label: str):
    request, _policy = _capture(label)
    return _expected_shard(request)


def _actual_shard_id_for_request(label: str) -> str:
    return _expected_shard_for_request(label).shard_id
