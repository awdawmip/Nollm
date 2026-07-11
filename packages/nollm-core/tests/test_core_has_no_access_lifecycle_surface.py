import nollm_core


def test_core_has_no_access_lifecycle_surface() -> None:
    forbidden = {"CoreClientLease", "client_kind", "acquire_client_lease", "release_client_lease", "transaction_lease"}
    assert forbidden.isdisjoint(nollm_core.__all__)
    assert forbidden.isdisjoint(vars(nollm_core.CoreRuntime))
