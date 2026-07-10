"""Host contract version registry and identity-preserving envelope migration."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .host_contract import CAPABILITIES, CONTRACT_VERSION, GRFHostRequest, SUPPORTED_CONTRACT_VERSIONS


@dataclass(frozen=True)
class ContractVersion:
    version: str
    status: str
    capabilities: tuple[str, ...]


class ContractVersionRegistry:
    def __init__(self) -> None:
        self._versions = {
            "grf_host_v1": ContractVersion("grf_host_v1", "supported_deprecated", CAPABILITIES),
            "grf_host_v2": ContractVersion("grf_host_v2", "current", CAPABILITIES),
        }

    def get(self, version: str) -> ContractVersion:
        try:
            return self._versions[version]
        except KeyError as exc:
            raise ValueError("unsupported GRF host contract version") from exc

    def current(self) -> ContractVersion:
        return self.get(CONTRACT_VERSION)

    def versions(self) -> tuple[ContractVersion, ...]:
        return tuple(self._versions[key] for key in sorted(self._versions))


def migrate_host_request(payload: dict[str, Any], target_version: str = CONTRACT_VERSION) -> dict[str, Any]:
    if target_version not in SUPPORTED_CONTRACT_VERSIONS:
        raise ValueError("unsupported migration target")
    source = GRFHostRequest.from_mapping(payload)
    migrated = deepcopy(payload)
    migrated["contract_version"] = target_version
    migrated["migration"] = {"from": source.contract_version, "to": target_version, "identity_preserved": True}
    GRFHostRequest.from_mapping(migrated)
    return migrated
