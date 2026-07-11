from nollm_core import (
    BridgeSpec,
    CoreRecallRequest,
    CoreRuntime,
    GeometryAddress,
    GeometryAnchor,
    MemoryAtom,
    RecallBudget,
)


def address(layer: int, q: int, r: int) -> GeometryAddress:
    return GeometryAddress("exact", "chart", layer, q, r)


def request(entry: GeometryAddress, kernels: tuple[str, ...], **changes: int) -> CoreRecallRequest:
    values = dict(max_steps=2, beam=32, max_layer_delta=3, max_lateral_ring=1, max_bridge_steps=2, max_results=32)
    values.update(changes)
    return CoreRecallRequest("recall", (entry,), kernels, RecallBudget(**values))


def test_explicit_cell_direct_lateral_coverage_and_bridge(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    entry = address(1, -2, 3)
    lateral = entry.lateral(1)[0]
    up = entry.coverage_up()[0]
    down = entry.coverage_down()[0]
    bridge_target = address(1, 9, -9)
    for atom_id, cell in (("direct", entry), ("lateral", lateral), ("up", up), ("down", down), ("bridge", bridge_target)):
        runtime.put(MemoryAtom(atom_id, atom_id), cell)
    runtime.bridge_add(
        BridgeSpec(
            "bridge",
            GeometryAnchor("from", (entry,)),
            GeometryAnchor("to", (bridge_target,)),
            1 << 15,
            "normal",
            1,
            2,
        )
    )
    result = runtime.recall(request(entry, ("lateral", "coverage_up", "coverage_down", "bridge")))
    assert {item.atom.atom_id for item in result.items} == {"direct", "lateral", "up", "down", "bridge"}
    assert result.items == tuple(sorted(result.items, key=lambda item: (-item.score_q16, item.handle.geometry_address.stable_key(), item.handle.local_atom_id)))


def test_recall_budget_empty_cell_and_no_identity_entry(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    entry = address(0, -11, 7)
    empty = runtime.recall(request(entry, (), max_steps=0))
    assert empty.items == ()
    runtime.put(MemoryAtom("far", "far"), entry.lateral(1)[0])
    exhausted = runtime.recall(request(entry, ("lateral",), max_steps=0))
    assert exhausted.items == ()
    assert exhausted.budget_exhausted
    assert not hasattr(runtime, "resolve_entry_by_shard")
    assert not hasattr(runtime, "get_by_global_id")
