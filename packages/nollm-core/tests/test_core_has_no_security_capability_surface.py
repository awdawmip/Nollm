import nollm_core


def test_core_has_no_security_capability_surface() -> None:
    forbidden = {"CoreTransaction", "FileCoreStateStore", "CellStore", "safe_emit", "ConsistentStatePort", "CoverageTemplateCompiler", "CompilerMetadata"}
    assert forbidden.isdisjoint(nollm_core.__all__)
    assert forbidden.isdisjoint(vars(nollm_core.CoreRuntime))
