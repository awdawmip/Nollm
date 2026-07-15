from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"), str(ROOT / "packages/nollm-access/src")]

from nollm_access import AccessDecision, AccessRuntime, FileHandleStore, FileStatementStore, MemoryStatement  # noqa: E402
from nollm_core import CoreRuntime, GeometryAddress, KernelRegistry  # noqa: E402


SCRIPT = ROOT / "lab/nollm-lab/m1/run_translation_normalized_workspace_migration.py"
SPEC = importlib.util.spec_from_file_location("translation_normalized_migration", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _seed_v4_workspace(root: Path) -> tuple[bytes, bytes]:
    statement = MemoryStatement("migration:statement", "migration content")
    address = GeometryAddress("default_dream_v1", "default", 0, -12, 9)
    with CoreRuntime(root) as core:
        with AccessRuntime(core, FileStatementStore(root), FileHandleStore(root)) as access:
            access.capture(statement)
            access.apply(AccessDecision("migration:decision", statement.statement_id, "new", address, reason_text="fixture", decided_by="fixture"))
    state_path = root / "core/current_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["geometry_registry"] = {
        **state["geometry_registry"],
        "profile_registry_version": MODULE.SOURCE_PROFILE_REGISTRY_VERSION,
        "kernel_registry_version": MODULE.SOURCE_KERNEL_REGISTRY_VERSION,
    }
    state_path.write_bytes(MODULE._canonical(state))
    return (root / "access/bindings.json").read_bytes(), next((root / "access/statements").rglob("*.json")).read_bytes()


def test_migration_preserves_access_bytes_and_reopens_current_core(tmp_path: Path) -> None:
    source, target = tmp_path / "v4", tmp_path / "v5"
    binding_bytes, statement_bytes = _seed_v4_workspace(source)

    receipt = MODULE.migrate(source, target)

    assert receipt["mapping"] == "physical_addresses_unchanged;geometry_registry_v4_to_v5"
    assert receipt["cell_count"] == 1
    assert receipt["atom_count"] == 1
    assert receipt["binding_count"] == 1
    assert (target / "access/bindings.json").read_bytes() == binding_bytes
    assert next((target / "access/statements").rglob("*.json")).read_bytes() == statement_bytes
    with CoreRuntime(target) as runtime:
        assert runtime.placement_count() == 1
        persisted = json.loads(runtime.export_state_bytes().decode("utf-8"))
        assert persisted["geometry_registry"] == KernelRegistry().state_identity


def test_migration_rejects_a_non_v4_source(tmp_path: Path) -> None:
    source, target = tmp_path / "v4", tmp_path / "v5"
    _seed_v4_workspace(source)
    state_path = source / "core/current_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["geometry_registry"] = KernelRegistry().state_identity
    state_path.write_bytes(MODULE._canonical(state))

    with pytest.raises(ValueError, match="translation-covariant"):
        MODULE.migrate(source, target)
    assert not target.exists()
