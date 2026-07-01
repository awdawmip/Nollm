"""Transport-neutral DI1 Integration Shell over sealed DR1 recall."""

from __future__ import annotations

from typing import Any

from nollm.dream_geometry import recall as recall_facade
from nollm.dream_geometry.cortex import CompiledQueryProbe
from nollm.dream_geometry.evidence import MemorySubstrateStore
from nollm.dream_geometry.recall import RecallPolicy, RecallUniverse, RuntimeTimeResolution

from .errors import DI1ErrorCode
from .public_recall_view import PublicViewError, public_recall_envelope
from .types import (
    CapabilitiesInvocation,
    IntegrationReadContext,
    IntegrationResponse,
    RecallInvocation,
    error_response,
    validate_request_id,
)


class IntegrationShell:
    """Call-local, read-only facade for capabilities and recall."""

    def capabilities(self, request_id: str) -> IntegrationResponse:
        if not validate_request_id(request_id):
            return error_response(request_id if isinstance(request_id, str) else None, "capabilities", DI1ErrorCode.invalid_invocation)
        return IntegrationResponse(
            True,
            request_id,
            "capabilities",
            result={
                "kind": "nollm_integration_capabilities",
                "capabilities": ["capabilities", "recall"],
                "input_contract": "typed_python_objects",
                "transport": "none",
                "read_only": True,
                "durable_objects": [],
            },
        )

    def handle(self, invocation: object, context: IntegrationReadContext | None = None) -> IntegrationResponse:
        request_id = getattr(invocation, "request_id", None)
        operation = getattr(invocation, "operation", None)
        if not isinstance(operation, str):
            return error_response(request_id if isinstance(request_id, str) else None, None, DI1ErrorCode.invalid_invocation)
        if not validate_request_id(request_id):
            return error_response(request_id if isinstance(request_id, str) else None, operation, DI1ErrorCode.invalid_invocation)
        if isinstance(invocation, CapabilitiesInvocation):
            if invocation.operation != "capabilities":
                return error_response(invocation.request_id, invocation.operation, DI1ErrorCode.operation_unsupported)
            return self.capabilities(invocation.request_id)
        if not isinstance(invocation, RecallInvocation):
            return error_response(request_id, operation, DI1ErrorCode.operation_unsupported if operation != "recall" else DI1ErrorCode.invalid_invocation)
        if invocation.operation != "recall":
            return error_response(invocation.request_id, invocation.operation, DI1ErrorCode.operation_unsupported)
        if not isinstance(invocation.query_probe, CompiledQueryProbe):
            return error_response(invocation.request_id, invocation.operation, DI1ErrorCode.invalid_invocation)
        if not _valid_read_context(context):
            return error_response(invocation.request_id, invocation.operation, DI1ErrorCode.invalid_read_context)
        try:
            digest = recall_facade.resolve_recall(
                invocation.query_probe,
                context.recall_universe,
                context.evidence_store,
                runtime_time=context.runtime_time,
                policy=context.recall_policy,
            )
            return IntegrationResponse(
                True,
                invocation.request_id,
                invocation.operation,
                result=public_recall_envelope(digest, context.evidence_store),
            )
        except PublicViewError as exc:
            return error_response(invocation.request_id, invocation.operation, exc.code)
        except Exception:
            return error_response(invocation.request_id, invocation.operation, DI1ErrorCode.internal_error)


def capabilities(request_id: str) -> IntegrationResponse:
    return IntegrationShell().capabilities(request_id)


def handle(invocation: object, context: IntegrationReadContext | None = None) -> IntegrationResponse:
    return IntegrationShell().handle(invocation, context)


def _valid_read_context(context: Any) -> bool:
    return (
        isinstance(context, IntegrationReadContext)
        and isinstance(context.evidence_store, MemorySubstrateStore)
        and isinstance(context.recall_universe, RecallUniverse)
        and (context.runtime_time is None or isinstance(context.runtime_time, RuntimeTimeResolution))
        and isinstance(context.recall_policy, RecallPolicy)
    )


__all__ = ["IntegrationShell", "capabilities", "handle"]
