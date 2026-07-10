"""Direct, non-semantic filesystem locations for GRF geometry objects."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from .cell_address import CellAddress
from .path_encoding import safe_object_path


PARTITION_WIDTH = 16


def partition_id(cell: CellAddress) -> tuple[int, int]:
    """Return the stable integer partition containing a cell, including negatives."""
    return (cell.q // PARTITION_WIDTH, cell.r // PARTITION_WIDTH)


def placement_path(root: Path, cell: CellAddress, placement_id: str) -> Path:
    partition_q, partition_r = partition_id(cell)
    return (
        Path(root)
        / "grfs"
        / "field"
        / _directory_component(cell.profile_id)
        / _directory_component(cell.chart_id)
        / str(cell.layer)
        / f"{partition_q}_{partition_r}"
        / f"{cell.q}_{cell.r}"
        / "placements"
        / safe_object_path("placement_record", placement_id)
    )


def evidence_path(root: Path, shard_id: str) -> Path:
    return Path(root) / "grfs" / "evidence" / "shards" / safe_object_path("evidence_shard", shard_id)


def admission_path(root: Path, admission_id: str) -> Path:
    return Path(root) / "grfs" / "admissions" / "minimal_records" / safe_object_path("minimal_admission_record", admission_id)


def source_manifest_path(root: Path, source_id: str) -> Path:
    return Path(root) / "grfs" / "manifests" / safe_object_path("source_manifest", source_id)


def _directory_component(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("geometry directory component must be non-empty text")
    return quote(value, safe="-_.")
