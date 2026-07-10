from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.grf.unified_scale_validation import run_unified_scale_validation  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--partition-size", type=int, default=100_000)
    parser.add_argument("--milestones", type=int, nargs="+", default=(10_000, 100_000, 1_000_000, 10_000_000))
    args = parser.parse_args()
    result = run_unified_scale_validation(tuple(args.milestones), args.partition_size).to_mapping()
    payload = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
