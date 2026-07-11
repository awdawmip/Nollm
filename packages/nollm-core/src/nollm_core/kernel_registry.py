from __future__ import annotations

from hashlib import sha256
import json

from .coverage_template import COVERAGE_DOWN, COVERAGE_UP, DEFAULT_FANOUT_LIMIT, LATERAL, CoverageTemplate, CoverageTemplateCompiler
from .profiles import PROFILE_REGISTRY_VERSION, profile_registry_digest, profiles

KERNEL_REGISTRY_VERSION = "nollm_geometry_kernels_v2"


class KernelRegistry:
    def __init__(self, fanout_limit: int = DEFAULT_FANOUT_LIMIT) -> None:
        self.fanout_limit = fanout_limit
        compiler = CoverageTemplateCompiler(fanout_limit)
        self._templates = {(profile.profile_id, direction): compiler.compile(profile.profile_id, direction) for profile in profiles() for direction in (COVERAGE_UP, COVERAGE_DOWN, LATERAL)}

    def coverage_template(self, profile_id: str, direction: str) -> CoverageTemplate:
        try:
            return self._templates[(profile_id, direction)]
        except KeyError as error:
            raise ValueError("unknown coverage template") from error

    def templates(self) -> tuple[CoverageTemplate, ...]:
        return tuple(self._templates[key] for key in sorted(self._templates))

    @property
    def identity(self) -> str:
        document = {"profile_digest": profile_registry_digest(), "fanout_limit": self.fanout_limit, "relation_semantics": {"registry": ["coverage_up", "coverage_down", "lateral"], "persistent": ["bridge_spec"]}, "templates": [template.to_mapping() for template in self.templates()]}
        return sha256(json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @property
    def state_identity(self) -> dict[str, str]:
        return {"profile_registry_version": PROFILE_REGISTRY_VERSION, "profile_registry_id": profile_registry_digest(), "kernel_registry_version": KERNEL_REGISTRY_VERSION, "kernel_registry_id": self.identity, "relation_semantics": "registry:coverage_up,coverage_down,lateral;state:bridge_spec"}
