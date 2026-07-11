import json

from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom
from nollm_trace import JsonlTraceSink, MetricsTraceSink, TraceInspector


def test_jsonl_metrics_and_inspector_are_trace_owned(tmp_path) -> None:
    path = tmp_path / "trace" / "events.jsonl"
    metrics = MetricsTraceSink()
    from nollm_trace import CompositeTraceSink

    core = CoreRuntime(tmp_path / "core", trace_sink=CompositeTraceSink(JsonlTraceSink(path), metrics))
    cell = GeometryAddress("eisenstein_exact_v1", "trace", 0, 0, 0)
    core.put(MemoryAtom("a", "payload"), cell)
    core.export_state_bytes()

    inspector = TraceInspector()
    records = inspector.read_jsonl(path)
    summary = inspector.summarize(records)
    assert summary == dict(sorted(metrics.counts.items()))
    assert summary["core.put"] == 1
    assert all("CoreRuntime" not in json.dumps(record, sort_keys=True) for record in records)


def test_deleting_trace_file_does_not_change_core(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    core = CoreRuntime(tmp_path / "core", trace_sink=JsonlTraceSink(path))
    handle = core.put(MemoryAtom("a", "payload"), GeometryAddress("eisenstein_exact_v1", "trace", 0, 0, 0))
    expected = core.export_state_bytes()
    path.unlink()
    assert core.get(handle).payload_utf8 == "payload"
    assert core.export_state_bytes() == expected
