from nollm_core import BridgeSpec, CoreRuntime, GeometryAddress, GeometryAnchor, MemoryAtom
from nollm_snapshot import SnapshotService


def test_store_runtime_and_snapshot_bytes_match_after_mutations(tmp_path) -> None:
    runtime = CoreRuntime(tmp_path)
    snapshot = SnapshotService()
    cell = GeometryAddress("eisenstein_exact_v1", "c", 0, 0, 0)
    handle = runtime.put(MemoryAtom("a", "one"), cell)
    for action in (
        lambda: runtime.replace(handle, "two"),
        lambda: runtime.bridge_add(BridgeSpec("b", GeometryAnchor("a", (cell,)), GeometryAnchor("z", (cell,)), 1, "normal", 1, 1)),
        lambda: runtime.bridge_remove("b"),
    ):
        action()
        assert runtime.store.read_bytes() == runtime.state_bytes() == snapshot.create(runtime)
