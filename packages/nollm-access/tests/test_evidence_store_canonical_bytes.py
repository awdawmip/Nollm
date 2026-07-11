import json

import pytest

from nollm_access import FileEvidenceStore, MemoryStatement


def test_evidence_rejects_noncanonical_and_extra_fields(tmp_path) -> None:
    store = FileEvidenceStore(tmp_path)
    store.put_original(MemoryStatement("s", "payload"))
    path = store._path("s")
    value = json.loads(path.read_bytes())
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match="canonical"):
        store.get_original("s")
    value["extra"] = 1
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        store.get_original("s")
