from __future__ import annotations

import hashlib
import json

from .coverage_template import COVERAGE_DOWN, COVERAGE_UP, CoverageTemplate, CoverageTemplateCompiler
from .profiles import PROFILE_REGISTRY_VERSION, profiles

KERNEL_REGISTRY_VERSION = "nollm_geometry_kernels_v1"


class KernelRegistry:
    def __init__(self) -> None:
        compiler = CoverageTemplateCompiler()
        self._templates = {(profile.profile_id, direction): compiler.compile(profile.profile_id, direction) for profile in profiles() for direction in (COVERAGE_UP, COVERAGE_DOWN)}

    def coverage_template(self, profile_id: str, direction: str) -> CoverageTemplate:
        try:
            return self._templates[(profile_id, direction)]
        except KeyError as error:
            raise ValueError("unknown coverage template") from error

    @property
    def identity(self) -> str:
        payload = [(key, [(entry.layer_delta, entry.dq, entry.dr, entry.weight_q16) for entry in value.entries]) for key, value in sorted(self._templates.items())]
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
        return hashlib.sha256(encoded).hexdigest()

    @property
    def state_identity(self) -> dict[str, str]:
        return {"profile_registry_version": PROFILE_REGISTRY_VERSION, "kernel_registry_version": KERNEL_REGISTRY_VERSION, "kernel_registry_id": self.identity}
