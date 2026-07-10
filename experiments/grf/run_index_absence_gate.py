"""Fail when active GRF code reintroduces forbidden semantic indexes."""

from __future__ import annotations

from pathlib import Path


FORBIDDEN = (
    "PlacementIndex", "CellRegistry", "GRFPlacementPolicy", "PlacementCandidateGenerator",
    "_by_shard", "_by_cell", "_cell_lookup_cache", "_unique_routes", "_shared_routes",
    "_cell_intervals", "_source_intervals", "placements_for_entry", "placement_id_for_shard",
)


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "reference" / "python" / "nollm" / "grf"
    matches = [f"{path}:{token}" for path in root.rglob("*.py") for token in FORBIDDEN if token in path.read_text(encoding="utf-8")]
    if matches:
        raise SystemExit("forbidden index symbols:\n" + "\n".join(matches))
    print("index absence gate passed")


if __name__ == "__main__":
    main()
