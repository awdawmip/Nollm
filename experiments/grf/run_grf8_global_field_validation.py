"""Global sharded-field lifecycle and bounded-directory validation for GRF8."""
from __future__ import annotations

import json

from nollm.grf.cell_address import CellAddress
from nollm.grf.global_field import GlobalFieldDirectory, partition_descriptor
from nollm.grf.grf7_incremental_validation import run_incremental_repartition_validation


def main() -> int:
    directory = GlobalFieldDirectory()
    descriptors = tuple(partition_descriptor(f"partition:grf8:{index}", index * 10, index * 10 + 9, index * 100, index * 100 + 99) for index in range(500))
    directory.add_many(descriptors)
    cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, 3456, 0)
    cell_hits = directory.locate_cell(cell)
    examined = directory.last_descriptors_examined
    source_hits = directory.locate_source(34_560)
    replayed = GlobalFieldDirectory.from_bytes(directory.canonical_bytes())
    incremental = run_incremental_repartition_validation()
    result = {
        "bounded_directory_lookup": bool(cell_hits) and examined < len(descriptors),
        "source_range_lookup": bool(source_hits),
        "directory_replay": replayed.canonical_bytes() == directory.canonical_bytes(),
        "cross_partition_replay": incremental.cross_partition_move_replayed,
        "bridge_rollback_removed": incremental.stitch_add_remove_replayed,
        "split_merge_no_dangling_bridge": incremental.split_merge_replayed,
        "incremental_equals_rebuild": incremental.incremental_equals_full_rebuild,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if all(result.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
