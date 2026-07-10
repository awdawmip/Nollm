"""Reusable conformance checks for replaceable GRF host adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AdapterConformanceResult:
    operation_surface_complete: bool
    mapping_only: bool
    owns_no_durable_facts: bool
    capability_mismatch_rejected: bool

    @property
    def passed(self) -> bool:
        return all((self.operation_surface_complete, self.mapping_only, self.owns_no_durable_facts, self.capability_mismatch_rejected))


class AdapterContractTestSuite:
    OPERATIONS = ("capture", "place", "admit", "recall", "validate")

    def run(self, adapter: Any) -> AdapterConformanceResult:
        surface = all(callable(getattr(adapter, operation, None)) for operation in self.OPERATIONS)
        mismatch = adapter.capture({"contract_version": "grf_host_v1", "capability": "recall", "payload": {}})
        attributes = vars(adapter)
        no_facts = not ({"evidence", "placements", "admissions", "recalls", "store", "field"} & set(attributes))
        mapping_only = callable(getattr(adapter, "handle_mapping", None))
        return AdapterConformanceResult(surface, mapping_only, no_facts, mismatch.get("error_code") == "adapter_capability_mismatch")
