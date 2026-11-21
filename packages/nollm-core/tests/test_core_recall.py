from nollm_core import (
    BridgeSpec,
    CoreRecallRequest,
    CoreRuntime,
    GeometryAddress,
    GeometryAnchor,
    MemoryAtom,
    RecallBudget,
)
from nollm_core import expand_template


def address(layer: int, q: int, r: int) -> GeometryAddress:
    return GeometryAddress("eisenstein_exact_v1", "chart", layer, q, r)


def request(entry: GeometryAddress, kernels: tuple[str, ...], **changes: int) -> CoreRecallRequest:
    values = dict(max_steps=2, beam=32, max_layer_delta=3, max_lateral_ring=1, max_bridge_steps=2, max_results=32)
    values.update(changes)
    return CoreRecallRequest("recall", (entry,), kernels, RecallBudget(**values))


def test_explicit_cell_direct_lateral_coverage_and_bridge(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    entry = address(1, -2, 3)
    lateral = entry.lateral(1)[0]
    up = expand_template(entry, runtime.kernel_registry.coverage_template(entry.profile_id, "coverage_up"))[0][0]
    down = expand_template(entry, runtime.kernel_registry.coverage_template(entry.profile_id, "coverage_down"))[0][0]
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
    result = runtime.recall(request(entry, ("bridge", "coverage_down", "coverage_up", "lateral")))
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


def test_lateral_revisits_do_not_spend_beam(tmp_path) -> None:
    class Trace:
        def __init__(self):
            self.frontier_sizes = []

        def emit(self, event):
            if event.name == "core.recall.frontier":
                self.frontier_sizes.append(event.fields["cell_count"])

    trace = Trace()
    runtime = CoreRuntime(tmp_path, trace_sink=trace)
    entry = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    second_ring = entry.lateral(2)
    for index, cell in enumerate(second_ring):
        runtime.put(MemoryAtom(f"ring2-{index}", "second ring"), cell)

    result = runtime.recall(request(entry, ("lateral",), beam=12, max_layer_delta=0))

    # The six first-ring cells converge on twelve new cells and seven revisits.
    # All twelve new cells fit without spending extra steps or beam slots.
    assert {item.handle.geometry_address for item in result.items} == set(second_ring)
    assert all(item.path == ("lateral", "lateral") for item in result.items)
    assert trace.frontier_sizes == [1, 6, 12]


def test_recall_keeps_improving_revisit(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    entry, intermediate, target = (address(0, q, 0) for q in (0, 10, 20))
    runtime.put(MemoryAtom("target", "target"), target)
    for name, source, destination, weight in (
        ("direct", entry, target, 1 << 14),
        ("first", entry, intermediate, 1 << 16),
        ("second", intermediate, target, 1 << 15),
    ):
        runtime.bridge_add(BridgeSpec(
            name, GeometryAnchor("from", (source,)), GeometryAnchor("to", (destination,)),
            weight, "normal", max_steps=2, max_fanout=1,
        ))

    result = runtime.recall(request(entry, ("bridge",), beam=2))

    assert [(item.atom.atom_id, item.score_q16, item.path) for item in result.items] == [
        ("target", 1 << 15, ("bridge", "bridge")),
    ]
    assert not result.budget_exhausted


def test_beam_clipping_reports_exhaustion_even_when_selected_branch_ends(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    entry = address(0, 0, 0)
    leaves = (address(0, 10, 0), address(0, 20, 0))
    for index, cell in enumerate(leaves):
        runtime.put(MemoryAtom(f"leaf-{index}", "leaf"), cell)
    runtime.bridge_add(BridgeSpec(
        "fork", GeometryAnchor("from", (entry,)), GeometryAnchor("to", leaves),
        1 << 15, "normal", max_steps=1, max_fanout=2,
    ))

    clipped = runtime.recall(request(entry, ("bridge",), beam=1, max_bridge_steps=1))
    complete = runtime.recall(request(entry, ("bridge",), beam=2, max_bridge_steps=1))

    assert [item.atom.atom_id for item in clipped.items] == ["leaf-0"]
    assert clipped.budget_exhausted
    assert {item.atom.atom_id for item in complete.items} == {"leaf-0", "leaf-1"}
    assert not complete.budget_exhausted


def test_terminal_revisits_and_out_of_layer_targets_do_not_report_exhaustion(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    entry, neighbor = address(0, 0, 0), address(0, 10, 0)
    runtime.put(MemoryAtom("neighbor", "neighbor"), neighbor)
    for name, source, target in (("out", entry, neighbor), ("back", neighbor, entry)):
        runtime.bridge_add(BridgeSpec(
            name, GeometryAnchor("from", (source,)), GeometryAnchor("to", (target,)),
            1 << 15, "normal", max_steps=2, max_fanout=1,
        ))

    kernels = ("bridge", "coverage_up")
    clipped = runtime.recall(request(entry, kernels, max_steps=0, max_layer_delta=0))
    complete = runtime.recall(request(entry, kernels, max_steps=1, max_layer_delta=0))

    assert clipped.items == ()
    assert clipped.budget_exhausted
    assert [item.atom.atom_id for item in complete.items] == ["neighbor"]
    assert not complete.budget_exhausted


def test_result_clipping_reports_exhaustion_without_propagation(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    entry = address(0, 0, 0)
    for index in range(3):
        runtime.put(MemoryAtom(f"atom-{index}", "occupied entry"), entry)

    clipped = runtime.recall(request(entry, (), max_steps=0, max_results=2))
    complete = runtime.recall(request(entry, (), max_steps=0, max_results=3))

    assert [item.atom.atom_id for item in clipped.items] == ["atom-0", "atom-1"]
    assert clipped.budget_exhausted
    assert len(complete.items) == 3
    assert not complete.budget_exhausted
