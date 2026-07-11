import json
from pathlib import Path

import nollm_core


ROOT = Path(__file__).resolve().parents[3]


def test_core_public_api_matches_allowlist() -> None:
    document = json.loads((ROOT / "docs/architecture/module-ownership/CORE_PUBLIC_API_ALLOWLIST.json").read_text(encoding="utf-8"))
    assert sorted(nollm_core.__all__) == document["symbols"]
    for name in document["symbols"]:
        assert hasattr(nollm_core, name)


def test_core_runtime_public_operations_match_allowlist() -> None:
    document = json.loads((ROOT / "docs/architecture/module-ownership/CORE_PUBLIC_API_ALLOWLIST.json").read_text(encoding="utf-8"))
    actual = sorted(
        name
        for name, value in vars(nollm_core.CoreRuntime).items()
        if not name.startswith("_") and callable(value)
    )
    assert actual == document["core_runtime_operations"]
