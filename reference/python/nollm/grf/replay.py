"""Replay helpers for file-first GRF workspaces."""

from __future__ import annotations

from pathlib import Path

from .coverage_template import COVERAGE_DOWN, COVERAGE_UP, LATERAL, CoverageTemplateCompiler
from .ledger import GRFLedger
from .recall import QueryProbe, resolve_grf_recall
from .relation_field import RelationField
from .storage import GRFFileStore


def load_all_grf_objects(workspace: Path) -> dict[str, tuple[object, ...]]:
    store = GRFFileStore(workspace)
    placements = tuple(store.read_placement_record(path.stem) for path in sorted((Path(workspace) / "grfs" / "placements" / "records").glob("*.json")))
    bridges = tuple(store.read_bridge_kernel(path.stem) for path in sorted((Path(workspace) / "grfs" / "patches" / "stitch" / "bridges").glob("*.json")))
    rejected = tuple(store.read_stitch_proposal(path.stem) for path in sorted((Path(workspace) / "grfs" / "patches" / "stitch" / "proposals").glob("*.json")) if store.read_stitch_proposal(path.stem).state == "rejected")
    return {"placements": placements, "bridges": bridges, "rejected_stitch_proposals": rejected}


def rebuild_relation_field_from_files(workspace: Path, recorded_at: str | None = None) -> RelationField:
    objects = load_all_grf_objects(workspace)
    compiler = CoverageTemplateCompiler()
    templates = (
        compiler.compile("eisenstein_exact_v1", COVERAGE_UP),
        compiler.compile("eisenstein_exact_v1", COVERAGE_DOWN),
        compiler.compile("eisenstein_exact_v1", LATERAL),
    )
    field = RelationField(templates, tuple(objects["bridges"]), tuple(objects["placements"]))
    if recorded_at is not None:
        GRFLedger(workspace).append("relation_field_rebuilt", "relation_field", "rf_rebuilt", Path("grfs/relation_fields/indexes"), "rebuilt", recorded_at)
    return field


def replay_recall(query: QueryProbe, workspace: Path, recorded_at: str | None = None):
    digest = resolve_grf_recall(query, rebuild_relation_field_from_files(workspace, recorded_at))
    if recorded_at is not None:
        GRFFileStore(workspace).write_recall_digest(digest, recorded_at)
    return digest
