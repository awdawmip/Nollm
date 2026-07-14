from __future__ import annotations

from hashlib import sha256
import json
from types import MappingProxyType

from .compiled_templates import COMPILED_TEMPLATES_JSON, COMPILED_TEMPLATES_SHA256
from .coverage_template import DEFAULT_FANOUT_LIMIT, CoverageTemplate, template_from_mapping
from .profiles import PROFILE_REGISTRY_VERSION, profile_registry_digest

KERNEL_REGISTRY_VERSION = "nollm_geometry_kernels_v3"


class KernelRegistry:
    def __init__(self, fanout_limit: int = DEFAULT_FANOUT_LIMIT) -> None:
        if fanout_limit != DEFAULT_FANOUT_LIMIT:
            raise ValueError("Core runtime uses the canonical compiled fanout limit")
        object.__setattr__(self, "fanout_limit", fanout_limit)
        if sha256(COMPILED_TEMPLATES_JSON).hexdigest() != COMPILED_TEMPLATES_SHA256:
            raise ValueError("compiled geometry template artifact digest mismatch")
        document = json.loads(COMPILED_TEMPLATES_JSON.decode("utf-8"))
        if document.get("schema_version") != "nollm_compiled_geometry_templates_v2":
            raise ValueError("unsupported compiled geometry template artifact")
        templates = tuple(template_from_mapping(value) for value in document["templates"])
        object.__setattr__(self, "_templates", MappingProxyType({(template.profile_id, template.direction, template.from_layer_mod): template for template in templates}))
        object.__setattr__(self, "compiled_artifact_sha256", COMPILED_TEMPLATES_SHA256)
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError("KernelRegistry is immutable")
        object.__setattr__(self, name, value)

    def coverage_template(self, profile_id: str, direction: str, from_layer: int = 0) -> CoverageTemplate:
        if type(from_layer) is not int:
            raise TypeError("from_layer must be an integer")
        from .profiles import runtime_profile
        phase = from_layer % runtime_profile(profile_id).phase_period
        try:
            return self._templates[(profile_id, direction, phase)]
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
