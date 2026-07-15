from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sys
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"), str(ROOT / "packages/nollm-access/src")]

from nollm_access import FileHandleStore, FileStatementStore  # noqa: E402
from nollm_core import CoreRuntime, KernelRegistry  # noqa: E402


SOURCE_GEOMETRY_REGISTRY = {
    "profile_registry_version": "nollm_geometry_profiles_v5",
    "profile_registry_id": "9da02fcc4a1fde39e4a32253079cc7db104eeea1b302e03cea5cecf24bb96cc3",
    "kernel_registry_version": "nollm_geometry_kernels_v5",
    "kernel_registry_id": "8a714b81b0f136de17939b552f5160274af5349c564a97946a87e1109f007e43",
    "relation_semantics": "dynamic:default_coverage_up,default_coverage_down;registry:legacy_coverage_up,legacy_coverage_down,lateral;state:bridge_spec",
}


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def _read_canonical(path: Path) -> tuple[dict[str, object], bytes]:
    payload = path.read_bytes()
    value = json.loads(payload.decode("utf-8"))
    if type(value) is not dict or _canonical(value) != payload:
        raise ValueError(f"noncanonical JSON: {path}")
    return value, payload


def _tree_sha256(root: Path) -> str:
    digest = sha256()
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big")); digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big")); digest.update(payload)
    return digest.hexdigest()


def migrate(source: Path, target: Path) -> dict[str, object]:
    source, target = source.resolve(), target.resolve()
    if not source.is_dir() or target.exists() or source == target:
        raise ValueError("source must exist and target must be a new distinct workspace")
    core, source_core_bytes = _read_canonical(source / "core/current_state.json")
    bindings, source_binding_bytes = _read_canonical(source / "access/bindings.json")
    if set(core) != {"schema_version", "geometry_registry", "cells", "bridges"} or core["schema_version"] != "nollm_core_state_v1":
        raise ValueError("source Core state schema is unsupported")
    if core["geometry_registry"] != SOURCE_GEOMETRY_REGISTRY:
        raise ValueError("source is not the accepted translation-normalized geometry registry")
    if type(core["cells"]) is not list or any(cell["address"].get("profile_id") != "default_dream_v1" for cell in core["cells"]):
        raise ValueError("source contains a non-default physical profile")
    if set(bindings) != {"schema_version", "bindings"} or bindings["schema_version"] != "nollm_access_bindings_v2":
        raise ValueError("source HandleStore schema is unsupported")

    upgraded = {**core, "geometry_registry": KernelRegistry().state_identity}
    temporary = target.parent / f".{target.name}.migration-{uuid4().hex}"
    try:
        temporary.mkdir(parents=True)
        shutil.copytree(source / "access", temporary / "access")
        (temporary / "core").mkdir()
        (temporary / "core/current_state.json").write_bytes(_canonical(upgraded))
        with CoreRuntime(temporary) as runtime:
            target_core_bytes = runtime.export_state_bytes()
            cells = runtime.occupied_cells()
            atom_count = runtime.placement_count()
        target_binding_bytes = FileHandleStore(temporary).state_bytes()
        statement_store = FileStatementStore(temporary)
        for binding in bindings["bindings"]:
            statement_store.get(binding["current_statement_id"])
            for statement_id in binding["supporting_statement_ids"]:
                statement_store.get(statement_id)
        receipt = {
            "schema_version": "nollm_bounded_approximate_workspace_migration_v1",
            "source_workspace": str(source),
            "target_workspace": str(target),
            "mapping": "physical_addresses_unchanged;geometry_registry_v5_to_v6",
            "source_core_sha256": sha256(source_core_bytes).hexdigest(),
            "source_bindings_sha256": sha256(source_binding_bytes).hexdigest(),
            "source_statements_tree_sha256": _tree_sha256(source / "access/statements"),
            "target_core_sha256": sha256(target_core_bytes).hexdigest(),
            "target_bindings_sha256": sha256(target_binding_bytes).hexdigest(),
            "target_statements_tree_sha256": _tree_sha256(temporary / "access/statements"),
            "cell_count": len(cells),
            "atom_count": atom_count,
            "binding_count": len(bindings["bindings"]),
            "statement_file_count": len(tuple((temporary / "access/statements").rglob("*.json"))),
            "bridge_count": len(upgraded["bridges"]),
        }
        if receipt["source_statements_tree_sha256"] != receipt["target_statements_tree_sha256"]:
            raise AssertionError("Statement bytes changed during migration")
        if source_binding_bytes != target_binding_bytes:
            raise AssertionError("HandleBinding bytes changed during migration")
        (temporary / "migration-receipt.json").write_bytes(_canonical(receipt))
        os.replace(temporary, target)
        return receipt
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(migrate(arguments.source, arguments.target), ensure_ascii=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
