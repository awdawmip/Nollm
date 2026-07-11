from concurrent.futures import ThreadPoolExecutor
from threading import Event

from nollm_access import AccessDecision, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress


def test_failed_transaction_cannot_erase_later_success(tmp_path) -> None:
    entered, release = Event(), Event()
    failures = {"a"}
    def before_replace(_path):
        if failures:
            failures.clear()
            entered.set()
            release.wait(5)
            raise OSError("once")
    core = CoreRuntime(tmp_path / "core")
    store = FileHandleStore(tmp_path, before_replace)
    a = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    b = AccessRuntime(core, FileEvidenceStore(tmp_path), store)
    for runtime, name in ((a, "a"), (b, "b")):
        runtime.capture(MemoryStatement(name, name))
    def apply(runtime, name, q):
        try:
            return runtime.apply(AccessDecision(name, name, "new", target_cell=GeometryAddress("eisenstein_exact_v1", "c", 0, q, 0), reason_text="fixture"))
        except OSError:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        failed = pool.submit(apply, a, "a", 0)
        assert entered.wait(5)
        succeeded = pool.submit(apply, b, "b", 1)
        release.set()
        assert failed.result() is None
        handle = succeeded.result()
    assert handle is not None and core.contains(handle) and store.get("b") == handle
