from __future__ import annotations

from dataclasses import replace

from nollm.dream_geometry.adapters import CapabilitiesInvocation, IntegrationReadContext, IntegrationShell, RecallInvocation
from nollm.dream_geometry.recall import RecallPolicy
from nollm.dream_geometry.validation.di1_integration_fixture import build_deferred_context, build_di1_context
from nollm.dream_geometry.validation.dr1_fixture import query_probe


def test_t_701_capabilities_returns_fixed_descriptor_without_context() -> None:
    response = IntegrationShell().handle(CapabilitiesInvocation("req-cap", "capabilities"))
    mapping = response.to_mapping()
    assert mapping["ok"] is True
    assert mapping["request_id"] == "req-cap"
    assert mapping["operation"] == "capabilities"
    assert mapping["result"]["capabilities"] == ["capabilities", "recall"]
    assert mapping["result"]["read_only"] is True


def test_t_702_recall_success_echoes_request_and_result_is_exclusive(tmp_path) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    mapping = IntegrationShell().handle(invocation, context).to_mapping()
    assert mapping["ok"] is True
    assert mapping["request_id"] == invocation.request_id
    assert mapping["operation"] == "recall"
    assert "result" in mapping
    assert "error" not in mapping
    assert mapping["result"]["status"] == "resolved"


def test_t_703_unknown_operation_returns_stable_error() -> None:
    mapping = IntegrationShell().handle(CapabilitiesInvocation("req-bad-op", "debug")).to_mapping()
    assert mapping["ok"] is False
    assert mapping["error"]["code"] == "DI1_OPERATION_UNSUPPORTED"
    assert "traceback" not in mapping["error"]["message"].lower()


def test_t_704_non_compiled_query_probe_is_invalid(tmp_path) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    bad = object.__new__(RecallInvocation)
    object.__setattr__(bad, "request_id", invocation.request_id)
    object.__setattr__(bad, "operation", "recall")
    object.__setattr__(bad, "query_probe", "raw text")
    mapping = IntegrationShell().handle(bad, context).to_mapping()
    assert mapping["ok"] is False
    assert mapping["error"]["code"] == "DI1_INVALID_INVOCATION"


def test_t_705_invalid_context_shape_is_rejected(tmp_path) -> None:
    _, _, universe, invocation, _ = build_di1_context(tmp_path)
    invalid = IntegrationReadContext("not-store", universe, None, RecallPolicy())
    mapping = IntegrationShell().handle(invocation, invalid).to_mapping()
    assert mapping["ok"] is False
    assert mapping["error"]["code"] == "DI1_INVALID_READ_CONTEXT"


def test_t_706_dr1_non_resolved_statuses_are_success_transport(tmp_path) -> None:
    _, _, _, invocation, context = build_deferred_context(tmp_path)
    deferred = IntegrationShell().handle(invocation, context).to_mapping()
    assert deferred["ok"] is True
    assert deferred["result"]["status"] == "deferred"
    bad_probe = replace(query_probe(), budget=replace(query_probe().budget, max_cells_per_layer=0))
    rejected = IntegrationShell().handle(RecallInvocation("req-rejected", "recall", bad_probe), context).to_mapping()
    assert rejected["ok"] is True
    assert rejected["result"]["status"] in {"deferred", "rejected"}
