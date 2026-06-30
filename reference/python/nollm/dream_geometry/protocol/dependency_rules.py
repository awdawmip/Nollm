"""Executable DG0 dependency firewall rules for Dream Geometry V2.

Allowed: centralize the V2 module dependency matrix for tests and future gates.
Forbidden: runtime probing, filesystem inspection, network access, subprocesses,
OpenClaw access, or duplicated business logic.
"""

from .contracts import DependencyRule, ModuleName

ALLOWED_DEPENDENCIES: frozenset[tuple[ModuleName, ModuleName]] = frozenset(
    {
        (ModuleName.evidence, ModuleName.protocol),
        (ModuleName.geometry, ModuleName.protocol),
        (ModuleName.cortex, ModuleName.protocol),
        (ModuleName.cortex, ModuleName.evidence),
        (ModuleName.field, ModuleName.protocol),
        (ModuleName.field, ModuleName.evidence),
        (ModuleName.field, ModuleName.geometry),
        (ModuleName.recall, ModuleName.protocol),
        (ModuleName.recall, ModuleName.evidence),
        (ModuleName.recall, ModuleName.geometry),
        (ModuleName.recall, ModuleName.field),
        (ModuleName.recall, ModuleName.cortex),
        (ModuleName.adapters, ModuleName.protocol),
        (ModuleName.adapters, ModuleName.evidence),
        (ModuleName.adapters, ModuleName.cortex),
        (ModuleName.adapters, ModuleName.recall),
        (ModuleName.validation, ModuleName.protocol),
        (ModuleName.validation, ModuleName.evidence),
        (ModuleName.validation, ModuleName.geometry),
        (ModuleName.validation, ModuleName.field),
        (ModuleName.validation, ModuleName.cortex),
        (ModuleName.validation, ModuleName.recall),
        (ModuleName.validation, ModuleName.adapters),
    }
)

FORBIDDEN_DEPENDENCIES: tuple[DependencyRule, ...] = (
    DependencyRule(ModuleName.geometry, ModuleName.cortex, False, "Geometry must not depend on semantic compilation."),
    DependencyRule(ModuleName.geometry, ModuleName.recall, False, "Geometry must not depend on recall."),
    DependencyRule(ModuleName.geometry, ModuleName.adapters, False, "Geometry must not depend on external shells."),
    DependencyRule(ModuleName.field, ModuleName.adapters, False, "Field must not depend on adapters."),
    DependencyRule(ModuleName.evidence, ModuleName.geometry, False, "Evidence persistence must not decide geometry."),
    DependencyRule(ModuleName.cortex, ModuleName.field, False, "Cortex submits proposals rather than mutating Field."),
    DependencyRule(ModuleName.adapters, ModuleName.geometry, False, "Adapters must not call geometry internals in DG0."),
)


def is_dependency_allowed(importer: ModuleName, imported: ModuleName) -> bool:
    """Return whether a V2 module import edge is allowed in DG0."""

    if importer == imported:
        return True
    if importer == ModuleName.protocol:
        return False
    return (importer, imported) in ALLOWED_DEPENDENCIES


DEPENDENCY_RULES: tuple[DependencyRule, ...] = tuple(
    DependencyRule(importer, imported, True, "Allowed by DG0 dependency DAG.")
    for importer, imported in sorted(ALLOWED_DEPENDENCIES, key=lambda item: (item[0].value, item[1].value))
) + FORBIDDEN_DEPENDENCIES


__all__ = [
    "ALLOWED_DEPENDENCIES",
    "DEPENDENCY_RULES",
    "FORBIDDEN_DEPENDENCIES",
    "is_dependency_allowed",
]
