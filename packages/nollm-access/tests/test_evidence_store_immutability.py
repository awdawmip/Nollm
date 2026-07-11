from concurrent.futures import ThreadPoolExecutor

from nollm_access import FileEvidenceStore, MemoryStatement


def test_concurrent_different_content_never_last_writer_wins(tmp_path) -> None:
    store = FileEvidenceStore(tmp_path)
    def put(content):
        try:
            store.put_original(MemoryStatement("s", content))
            return "ok"
        except FileExistsError:
            return "exists"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(put, ("one", "two")))
    assert sorted(results) == ["exists", "ok"]
    assert store.get_original("s").content_utf8 in {"one", "two"}
