from nollm_core import (
    BridgeSpec,
    CoreRecallRequest,
    CoreRuntime,
    GeometryAddress,
    GeometryAnchor,
    MemoryAtom,
    NullTraceSink,
    RecallBudget,
    TraceEvent,
)
from nollm_trace import CompositeTraceSink, MemoryTraceSink


class FailingTraceSink:
    def emit(self, event: TraceEvent) -> None:
        raise RuntimeError(event.name)


def cell(q: int, r: int) -> GeometryAddress:
    return GeometryAddress("eisenstein_exact_v1", "chart", 1, q, r)


def run_sequence(tmp_path, name: str, sink: object) -> tuple[object, ...]:
    core = CoreRuntime(tmp_path / name, trace_sink=sink)
    first = core.put(MemoryAtom("first", "one"), cell(0, 0))
    second = core.put(MemoryAtom("second", "two"), cell(1, 0))
    core.replace(first, "one-replaced")
    moved = core.move(second, cell(2, -1))
    bridge = BridgeSpec(
        "bridge",
        GeometryAnchor("from", (cell(0, 0),)),
        GeometryAnchor("to", (cell(2, -1),)),
        1 << 15,
        "normal",
        1,
        2,
    )
    core.bridge_add(bridge)
    recall = core.recall(
        CoreRecallRequest(
            "recall",
            (cell(0, 0),),
            ("bridge",),
            RecallBudget(1, 4, 1, 0, 1, 4),
        )
    )
    token = core.begin_consistent_read()
    try:
        snapshot = core.export_state(token)
    finally:
        core.end_consistent_read(token)
    core.bridge_remove("bridge")
    return core.state_bytes(), first, moved, recall, snapshot


def test_trace_failure_never_changes_new_core_results(tmp_path) -> None:
    null_result = run_sequence(tmp_path, "null", NullTraceSink())
    memory = MemoryTraceSink()
    memory_result = run_sequence(tmp_path, "memory", memory)
    failing_result = run_sequence(tmp_path, "failing", FailingTraceSink())
    composite_memory = MemoryTraceSink()
    composite_result = run_sequence(
        tmp_path,
        "composite",
        CompositeTraceSink(FailingTraceSink(), composite_memory),
    )
    assert null_result == memory_result == failing_result == composite_result
    names = {event.name for event in memory.events}
    assert {
        "core.put",
        "core.replace",
        "core.move",
        "core.batch.begin",
        "core.batch.commit",
        "core.bridge.add",
        "core.bridge.remove",
        "core.recall.begin",
        "core.recall.end",
        "core.snapshot.freeze",
        "core.snapshot.release",
    } <= names
    assert composite_memory.events
