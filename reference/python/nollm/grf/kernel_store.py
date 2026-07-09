"""In-memory GRF template store."""

from __future__ import annotations

from dataclasses import dataclass

from .coverage_template import CoverageTemplate


@dataclass(frozen=True, order=True)
class TemplateKey:
    profile_id: str
    direction: str
    from_layer_mod: int
    source_phase: str | None


class InMemoryKernelStore:
    def __init__(self, templates: tuple[CoverageTemplate, ...] = ()) -> None:
        self._templates = {_key(template): template for template in templates}

    def put(self, template: CoverageTemplate) -> None:
        self._templates[_key(template)] = template

    def get(self, profile_id: str, direction: str, from_layer_mod: int = 0, source_phase: str | None = None) -> CoverageTemplate:
        return self._templates[TemplateKey(profile_id, direction, from_layer_mod, source_phase)]


def _key(template: CoverageTemplate) -> TemplateKey:
    return TemplateKey(template.profile_id, template.direction, template.from_layer_mod, template.source_phase)
