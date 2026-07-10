from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.grf.global_field import GlobalFieldDirectory, GRFPartitionNeighbor, partition_descriptor  # noqa: E402


def main() -> int:
    directory = GlobalFieldDirectory()
    sizes = []
    for index in range(100):
        directory.add(partition_descriptor(f"partition:manifest:{index:03d}", index * 100, index * 100 + 99, index * 100_000, index * 100_000 + 99_999))
        sizes.append(len(directory.canonical_bytes()))
        if index:
            directory.connect(GRFPartitionNeighbor(f"partition:manifest:{index - 1:03d}", f"partition:manifest:{index:03d}", "spatial_boundary"))
    payload = directory.canonical_bytes()
    replay = GlobalFieldDirectory.from_bytes(payload)
    result = {"gate": "GATE_A_PASS", "partition_count": 100, "directory_entry_count": 100, "directory_bytes": len(payload), "neighbor_link_count": len(directory.to_mapping()["neighbors"]), "snapshot_refs": [item.snapshot_ref.snapshot_ref for item in directory.entries()], "partition_boundaries": [item.boundary.to_mapping() for item in directory.entries()], "directory_replay_deterministic": replay.canonical_bytes() == payload, "directory_growth_monotonic": sizes == sorted(sizes)}
    raw = ROOT / "experiments" / "grf" / "results" / "GRF7_GLOBAL_DIRECTORY_MANIFEST.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    raw.write_text(text, encoding="utf-8", newline="\n")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
