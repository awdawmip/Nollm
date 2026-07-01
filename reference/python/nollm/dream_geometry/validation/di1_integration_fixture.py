"""Synthetic DI1 Integration Shell fixtures for validation and tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from nollm.dream_geometry.adapters import IntegrationReadContext, RecallInvocation
from nollm.dream_geometry.protocol.contracts import UsageState
from nollm.dream_geometry.recall import RecallPolicy
from nollm.dream_geometry.validation.dr1_fixture import build_fixture, query_probe, relative_time_resolution


def build_di1_context(root: Path, *, usage_state: UsageState = UsageState.active, runtime_time: bool = True):
    store, proposal, universe = build_fixture(root, usage_state=usage_state)
    context = IntegrationReadContext(
        store,
        universe,
        relative_time_resolution() if runtime_time else None,
        RecallPolicy(),
    )
    invocation = RecallInvocation("req-di1-fixture-001", "recall", query_probe())
    return store, proposal, universe, invocation, context


def build_deferred_context(root: Path):
    store, proposal, universe, invocation, context = build_di1_context(root, runtime_time=False)
    return store, proposal, universe, invocation, replace(context, runtime_time=None)


__all__ = ["build_deferred_context", "build_di1_context"]
