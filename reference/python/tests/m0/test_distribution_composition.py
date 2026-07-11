import importlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
MANIFESTS = ROOT / "distributions"


def load(name: str) -> dict[str, object]:
    return json.loads((MANIFESTS / name / "manifest.json").read_text(encoding="utf-8"))


def resolve(symbol: str) -> object:
    module_name, attribute = symbol.rsplit(".", 1)
    return getattr(importlib.import_module(module_name), attribute)


def test_distribution_manifests_have_finite_schema() -> None:
    for path in sorted(MANIFESTS.glob("*/manifest.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        assert type(value) is dict
        assert value["name"] == path.parent.name
        assert "runtime" in value or "extends" in value
        if "runtime" in value:
            assert type(value["runtime"]) is list
            assert all(type(item) is str and item for item in value["runtime"])
        if "extends" in value:
            assert type(value["extends"]) is str and value["extends"]


def test_bare_minimal_and_debug_composition_imports() -> None:
    bare, minimal, debug = load("nollm-bare"), load("nollm-minimal"), load("nollm-debug")
    assert bare["runtime"] == ["nollm-core"]
    assert resolve(bare["entrypoint"]).__name__ == "CoreRuntime"
    assert minimal["runtime"] == ["nollm-core", "nollm-snapshot", "nollm-access"]
    for symbol in minimal["defaults"][:-1]:
        resolve(symbol)
    assert minimal["defaults"][-1] == "trace=None"
    assert debug["extends"] == "nollm-minimal"
    assert debug["runtime"] == ["nollm-trace"]
    assert all(item.startswith("lab/") for item in debug["development"])
