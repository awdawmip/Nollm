"""File-shaped JSON adapter; all GRF work crosses the host contract."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter_ns
from typing import Any

from nollm.grf.host_contract import GRFHostRequest, GRFHostService, UnsupportedCapabilityError
from .grf_adapter_contract import GRFAdapterOperations


class GRFFileAdapter(GRFAdapterOperations):
    def __init__(self, workspace: Path) -> None:
        self._service = GRFHostService(Path(workspace))

    def handle_mapping(self, payload: dict[str, Any]) -> dict[str, object]:
        started = perf_counter_ns()
        try:
            response = self._service.handle(GRFHostRequest.from_mapping(payload))
            result = response.to_mapping()
            result["adapter_latency_ns"] = perf_counter_ns() - started
            return result
        except (UnsupportedCapabilityError, TypeError, ValueError):
            return {"contract_version": "grf_host_v1", "ok": False, "error_code": "adapter_request_error", "adapter_latency_ns": perf_counter_ns() - started}
        except Exception:
            return {"contract_version": "grf_host_v1", "ok": False, "error_code": "adapter_failure", "adapter_latency_ns": perf_counter_ns() - started}
