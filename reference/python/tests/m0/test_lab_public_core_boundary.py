import ast
import json
from pathlib import Path

import nollm_core


ROOT = Path(__file__).resolve().parents[4]


def test_lab_imports_no_nollm_core_private_submodules() -> None:
    findings = []
    for path in (ROOT / "lab/nollm-lab").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                findings.extend(alias.name for alias in node.names if alias.name.startswith("nollm_core."))
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("nollm_core."):
                findings.append(node.module)
    assert findings == []


def test_core_public_api_not_expanded_for_lab() -> None:
    allowlist = json.loads((ROOT / "docs/architecture/module-ownership/CORE_PUBLIC_API_ALLOWLIST.json").read_text(encoding="utf-8"))
    assert sorted(nollm_core.__all__) == allowlist["symbols"]
    for private_helper in ("AxialCoord", "CompilerMetadata", "normalize_q16_weights", "canonical_state_bytes", "COMPILED_TEMPLATES_JSON"):
        assert private_helper not in nollm_core.__all__
