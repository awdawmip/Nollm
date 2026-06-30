"""Strict caller-supplied relative-time projection validation for DR1."""

from __future__ import annotations

from nollm.dream_geometry.cortex.types import CompiledQueryProbe, TextSpanRef

from .projection import EXPLICIT_IN_QUERY
from .types import RecallValidationError, RuntimeTimeResolution


def validate_runtime_time_resolution(probe: CompiledQueryProbe, runtime_time: RuntimeTimeResolution | None) -> tuple[str, ...]:
    relative_entries = _relative_entries(probe)
    if not relative_entries:
        if runtime_time is not None:
            raise RecallValidationError("DR1_RUNTIME_TIME_FOR_NON_RELATIVE_QUERY", "runtime resolution supplied without relative_time query axis")
        return ()
    if runtime_time is None or not runtime_time.complete:
        return ("DEFERRED_TIME_RESOLUTION_REQUIRED",)
    if not runtime_time.spans:
        return ("DEFERRED_TIME_RESOLUTION_REQUIRED",)
    expected = {(step_id, start, end, text) for step_id, start, end, text in relative_entries}
    seen: set[tuple[str, int, int, str]] = set()
    for span in runtime_time.spans:
        key = (span.source_step_id, span.start_char, span.end_char, span.quoted_text)
        if key not in expected:
            raise RecallValidationError("DR1_RELATIVE_TIME_SPAN_MISMATCH", f"unmatched runtime span {key}")
        if key in seen:
            raise RecallValidationError("DR1_RELATIVE_TIME_DUPLICATE_RESOLUTION", f"duplicate runtime span {key}")
        if not span.resolved_axis_id or not span.resolved_expression:
            raise RecallValidationError("DR1_RELATIVE_TIME_INCOMPLETE_RESOLUTION", "resolved axis and expression are required")
        seen.add(key)
    if seen != expected:
        return ("DEFERRED_TIME_RESOLUTION_REQUIRED",)
    return ()


def _relative_entries(probe: CompiledQueryProbe) -> tuple[tuple[str, int, int, str], ...]:
    entries = []
    for axis in probe.axes:
        if axis.axis_id != "relative_time" or not axis.ray:
            continue
        step = axis.ray[0]
        basis = step.basis.value if hasattr(step.basis, "value") else str(step.basis)
        if basis != EXPLICIT_IN_QUERY:
            continue
        text_refs = [ref for ref in step.basis_refs if isinstance(ref, TextSpanRef)]
        if len(text_refs) != 1:
            raise RecallValidationError("DR1_RELATIVE_TIME_SPAN_INVALID", f"relative step {step.step_id} requires one TextSpanRef")
        ref = text_refs[0]
        if step.expression != ref.quoted_text:
            raise RecallValidationError("DR1_RELATIVE_TIME_SPAN_INVALID", f"relative step {step.step_id} does not match quoted text")
        entries.append((step.step_id, ref.start_char, ref.end_char, ref.quoted_text))
    return tuple(entries)


__all__ = ["validate_runtime_time_resolution"]
