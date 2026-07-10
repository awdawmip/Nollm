"""Cold/warm geometry recall validation without any semantic route index."""

from __future__ import annotations

from tempfile import TemporaryDirectory
from pathlib import Path

from nollm.grf.cell_address import CellAddress
from nollm.grf.facade import GRFFacade
from nollm.grf.recall import QueryProbe, RecallBudget


def main() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        facade = GRFFacade(root)
        receipt = facade.capture_text("capture:recall", "exact retained evidence", "window:recall", "2026-07-11T00:00:00Z")
        cell = CellAddress("eisenstein_exact_v1", "chart:recall", 0, -1, 2)
        facade.admit(receipt.shard_id or "", "window:recall", {"action": "place", "decision_id": "decision:recall", "candidate_id": "candidate:recall", "placement_id": "placement:recall", "selected_cell": cell.to_mapping()}, "2026-07-11T00:00:01Z")
        query = QueryProbe("query:recall", "explicit_cell", cell, ("coverage_up", "coverage_down", "lateral", "bridge"), RecallBudget(0, 1, 0, 0, 0, 8))
        cold = facade.recall(query)
        warm = facade.recall(query)
        assert cold.selected_shards == warm.selected_shards == (receipt.shard_id,)
        assert not (root / "grfs" / "placements" / "records").exists()
    print("geometry native cold/warm recall validation passed")


if __name__ == "__main__":
    main()
