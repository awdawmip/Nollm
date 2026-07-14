from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"), str(ROOT / "packages/nollm-access/src")]

from nollm_access import FileHandleStore, FileStatementStore  # noqa: E402
from nollm_core import CoreRuntime, KernelRegistry  # noqa: E402


OLD_PROFILE = "eisenstein_exact_v1"
NEW_PROFILE = "default_dream_v1"
CHART = "default"
LAYER = 0


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def _read_canonical(path: Path) -> tuple[dict[str, object], bytes]:
    payload = path.read_bytes()
    value = json.loads(payload.decode("utf-8"))
    if type(value) is not dict or _canonical(value) != payload:
        raise ValueError(f"noncanonical JSON: {path}")
    return value, payload


def _map_address(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != {"profile_id", "chart_id", "layer", "q", "r", "phase"}:
        raise ValueError("migration address fields are invalid")
    if (
        value["profile_id"] != OLD_PROFILE
        or value["chart_id"] != CHART
        or value["layer"] != LAYER
        or value["phase"] is not None
        or type(value["q"]) is not int
        or type(value["r"]) is not int
    ):
        raise ValueError("migration requires only eisenstein_exact_v1/default/layer0 addresses")
    return {**value, "profile_id": NEW_PROFILE}


def _map_anchor(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != {"anchor_id", "cells"} or type(value["cells"]) is not list:
        raise ValueError("migration bridge anchor is invalid")
    cells = [_map_address(item) for item in value["cells"]]
    cells.sort(key=_address_key)
    return {"anchor_id": value["anchor_id"], "cells": cells}


def _address_key(value: dict[str, object]) -> tuple[object, ...]:
    return (value["profile_id"], value["chart_id"], value["layer"], value["q"], value["r"], -1)


def _transform_core(document: dict[str, object]) -> dict[str, object]:
    if set(document) != {"schema_version", "geometry_registry", "cells", "bridges"}:
        raise ValueError("old Core state fields are invalid")
    if document["schema_version"] != "nollm_core_state_v1" or type(document["cells"]) is not list or type(document["bridges"]) is not list:
        raise ValueError("old Core state schema is unsupported")
    cells = []
    for cell in document["cells"]:
        if type(cell) is not dict or set(cell) != {"address", "atoms"} or type(cell["atoms"]) is not list or not cell["atoms"]:
            raise ValueError("old Core cell is invalid")
        cells.append({"address": _map_address(cell["address"]), "atoms": cell["atoms"]})
    cells.sort(key=lambda item: _address_key(item["address"]))
    bridges = []
    for bridge in document["bridges"]:
        if type(bridge) is not dict or set(bridge) != {"bridge_id", "from_anchor", "to_anchor", "weight_q16", "bridge_class", "max_steps", "max_fanout"}:
            raise ValueError("old Core bridge is invalid")
        bridges.append({**bridge, "from_anchor": _map_anchor(bridge["from_anchor"]), "to_anchor": _map_anchor(bridge["to_anchor"])})
    bridges.sort(key=lambda item: item["bridge_id"])
    return {
        "schema_version": document["schema_version"],
        "geometry_registry": KernelRegistry().state_identity,
        "cells": cells,
        "bridges": bridges,
    }


def _transform_bindings(document: dict[str, object]) -> dict[str, object]:
    if set(document) != {"schema_version", "bindings"} or document["schema_version"] != "nollm_access_bindings_v2" or type(document["bindings"]) is not list:
        raise ValueError("old HandleStore state is invalid")
    bindings = []
    for binding in document["bindings"]:
        if type(binding) is not dict or set(binding) != {"handle", "current_statement_id", "supporting_statement_ids"}:
            raise ValueError("old HandleBinding is invalid")
        handle = binding["handle"]
        if type(handle) is not dict or set(handle) != {"geometry_address", "local_atom_id"}:
            raise ValueError("old AtomHandle is invalid")
        bindings.append({**binding, "handle": {**handle, "geometry_address": _map_address(handle["geometry_address"])}})
    bindings.sort(key=lambda item: (*_address_key(item["handle"]["geometry_address"]), item["handle"]["local_atom_id"]))
    return {"schema_version": document["schema_version"], "bindings": bindings}


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
    core, old_core_bytes = _read_canonical(source / "core/current_state.json")
    bindings, old_binding_bytes = _read_canonical(source / "access/bindings.json")
    new_core = _transform_core(core)
    new_bindings = _transform_bindings(bindings)
    core_handles = {
        (*_address_key(cell["address"]), atom["local_atom_id"])
        for cell in new_core["cells"]
        for atom in cell["atoms"]
    }
    binding_handles = {
        (*_address_key(item["handle"]["geometry_address"]), item["handle"]["local_atom_id"])
        for item in new_bindings["bindings"]
    }
    if core_handles != binding_handles:
        raise ValueError("Core atoms and HandleBindings do not have identical migrated identities")
    temporary = target.parent / f".{target.name}.migration-{uuid4().hex}"
    try:
        temporary.mkdir(parents=True)
        shutil.copytree(source / "access", temporary / "access")
        (temporary / "core").mkdir()
        (temporary / "core/current_state.json").write_bytes(_canonical(new_core))
        (temporary / "access/bindings.json").write_bytes(_canonical(new_bindings))
        with CoreRuntime(temporary) as runtime:
            reopened_core = runtime.export_state_bytes()
            placement_count = runtime.placement_count()
        reopened_bindings = FileHandleStore(temporary).state_bytes()
        statement_files = tuple(sorted((temporary / "access/statements").rglob("*.json")))
        for item in new_bindings["bindings"]:
            FileStatementStore(temporary).get(item["current_statement_id"])
            for statement_id in item["supporting_statement_ids"]:
                FileStatementStore(temporary).get(statement_id)
        receipt = {
            "schema_version": "nollm_rotated_layer0_workspace_migration_v1",
            "source_workspace": str(source),
            "target_workspace": str(target),
            "mapping": f"{OLD_PROFILE}/{CHART}/layer0/q/r->{NEW_PROFILE}/{CHART}/layer0/q/r",
            "source_core_sha256": sha256(old_core_bytes).hexdigest(),
            "source_bindings_sha256": sha256(old_binding_bytes).hexdigest(),
            "source_statements_tree_sha256": _tree_sha256(source / "access/statements"),
            "target_core_sha256": sha256(reopened_core).hexdigest(),
            "target_bindings_sha256": sha256(reopened_bindings).hexdigest(),
            "target_statements_tree_sha256": _tree_sha256(temporary / "access/statements"),
            "cell_count": len(new_core["cells"]),
            "atom_count": placement_count,
            "binding_count": len(new_bindings["bindings"]),
            "statement_file_count": len(statement_files),
            "bridge_count": len(new_core["bridges"]),
        }
        if receipt["source_statements_tree_sha256"] != receipt["target_statements_tree_sha256"]:
            raise AssertionError("Statement bytes changed during migration")
        (temporary / "migration-receipt.json").write_bytes(_canonical(receipt))
        os.replace(temporary, target)
        return receipt
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _fixture(root: Path, layer: int = 0) -> None:
    address = {"profile_id": OLD_PROFILE, "chart_id": CHART, "layer": layer, "q": 2, "r": -1, "phase": None}
    atom_id = "fixture:atom"
    core = {
        "schema_version": "nollm_core_state_v1",
        "geometry_registry": {"historical": "migration-input-only"},
        "cells": [{"address": address, "atoms": [{"local_atom_id": atom_id, "atom": {"atom_id": atom_id, "payload_utf8": "fixture"}}]}],
        "bridges": [],
    }
    binding = {"schema_version": "nollm_access_bindings_v2", "bindings": [{"handle": {"geometry_address": address, "local_atom_id": atom_id}, "current_statement_id": atom_id, "supporting_statement_ids": []}]}
    (root / "core").mkdir(parents=True)
    (root / "access").mkdir(parents=True)
    (root / "core/current_state.json").write_bytes(_canonical(core))
    (root / "access/bindings.json").write_bytes(_canonical(binding))
    FileStatementStore(root).put(__import__("nollm_access").MemoryStatement(atom_id, "fixture"))


def self_check() -> dict[str, object]:
    with TemporaryDirectory(prefix="nollm-layer0-migration-") as temporary:
        root = Path(temporary)
        source, target = root / "old", root / "new"
        _fixture(source)
        receipt = migrate(source, target)
        with CoreRuntime(target) as runtime:
            profiles = {cell.profile_id for cell in runtime.occupied_cells()}
        blocked = root / "blocked"
        _fixture(blocked, layer=1)
        try:
            migrate(blocked, root / "must-not-exist")
        except ValueError as exc:
            nonzero_blocked = "layer0" in str(exc)
        else:
            nonzero_blocked = False
        checks = {
            "canonical_reopen": profiles == {NEW_PROFILE},
            "statement_bytes_preserved": receipt["source_statements_tree_sha256"] == receipt["target_statements_tree_sha256"],
            "nonzero_layer_blocked": nonzero_blocked,
            "failed_target_absent": not (root / "must-not-exist").exists(),
        }
        if not all(checks.values()):
            raise AssertionError(checks)
        return {"schema_version": "nollm_rotated_layer0_workspace_migration_check_v1", "checks": checks}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if (args.source is None) != (args.target is None):
        parser.error("--source and --target must be supplied together")
    result = migrate(args.source, args.target) if args.source is not None else self_check()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
