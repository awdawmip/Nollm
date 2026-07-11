import pytest
from nollm_core import KernelRegistry

def test_registry_is_deeply_immutable_and_mapping_does_not_alias() -> None:
    registry = KernelRegistry(); identity = registry.identity
    template = registry.coverage_template("eisenstein_exact_v1", "coverage_up")
    mapping = template.to_mapping(); mapping["compiler"]["fanout_limit"] = 999
    assert registry.identity == identity and template.compiler.fanout_limit == 7
    with pytest.raises(AttributeError): registry.fanout_limit = 9
