from dataclasses import fields

import nollm_core


FORBIDDEN = {
    "get_by_global_id",
    "search_by_source",
    "search_by_topic",
    "search_history",
    "capture",
    "admit",
    "promote",
    "revision",
    "rank_by_importance",
    "semantic_search",
    "embedding_search",
    "find_similar",
    "resolve_entry_by_shard",
    "resolve_entry_by_source",
}


def test_core_has_no_semantic_or_global_lookup_surface() -> None:
    assert FORBIDDEN.isdisjoint(set(dir(nollm_core.CoreRuntime)))
    assert {field.name for field in fields(nollm_core.MemoryAtom)} == {"atom_id", "payload_utf8"}
    assert "evidence_refs" not in {field.name for field in fields(nollm_core.BridgeSpec)}


def test_core_imports_no_product_package() -> None:
    assert not any(name.startswith("nollm_access") for name in vars(nollm_core))
    source = __import__("inspect").getsource(nollm_core.CoreRuntime)
    assert "PlacementRecord" not in source
    assert not hasattr(nollm_core, "CellStore")
    assert all(term not in source for term in ("relation_index", "semantic_search", "embedding"))
