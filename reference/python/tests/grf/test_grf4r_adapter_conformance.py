from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf_adapter_conformance import AdapterContractTestSuite
from integrations.adapters.grf_declared_host_adapter import GRFDeclaredHostAdapter
from integrations.adapters.grf_file_adapter import GRFFileAdapter


def test_all_adapters_pass_replaceable_contract_suite(tmp_path: Path) -> None:
    integrations = ROOT / "integrations"
    adapters = (
        GRFFileAdapter(tmp_path / "file"),
        GRFDeclaredHostAdapter(tmp_path / "openclaw", integrations / "openclaw" / "v2-adapter" / "capabilities.json"),
        GRFDeclaredHostAdapter(tmp_path / "codex", integrations / "codex" / "adapter" / "capabilities.json"),
    )
    suite = AdapterContractTestSuite()
    assert all(suite.run(adapter).passed for adapter in adapters)


def test_adapter_modules_contain_no_domain_or_semantic_memory_imports() -> None:
    forbidden = {"storage", "evidence", "placement", "admission", "relation_field", "recall", "embedding", "semantic"}
    for name in ("grf_file_adapter.py", "grf_declared_host_adapter.py", "grf_adapter_contract.py"):
        tree = ast.parse((ROOT / "integrations" / "adapters" / name).read_text(encoding="utf-8"))
        imported = {alias.name.rsplit(".", 1)[-1] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imported |= {node.module.rsplit(".", 1)[-1] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert not (forbidden & imported)
