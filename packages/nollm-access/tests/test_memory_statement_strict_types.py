import pytest

from nollm_access import MemoryStatement


@pytest.mark.parametrize("value", [123, True, {}, []])
def test_memory_statement_rejects_non_string_content(value) -> None:
    with pytest.raises(TypeError):
        MemoryStatement("s", value)


def test_mapping_never_coerces_context_refs() -> None:
    with pytest.raises(TypeError):
        MemoryStatement.from_mapping({"statement_id": "s", "content_utf8": "p", "source_handle": None, "context_refs": [1]})
