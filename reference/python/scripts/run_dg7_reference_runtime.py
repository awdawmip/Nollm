from __future__ import annotations

import argparse
from pathlib import Path
import sys

from nollm.dream_geometry.validation.dg7 import DG7RuntimeVerificationError, canonical_json, run_reference_runtime
from nollm.dream_geometry.validation.dg7.runner import error_mapping, receipt_to_mapping


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--work-root")
    parser.add_argument("--scenario")
    args = parser.parse_args()

    if not args.output:
        sys.stdout.write(canonical_json(error_mapping("DG7_INVALID_SCENARIO", "missing explicit output path")))
        return 2
    if not args.work_root:
        sys.stdout.write(canonical_json(error_mapping("DG7_INVALID_WORK_ROOT", "missing explicit work root")))
        return 2
    if not args.scenario:
        sys.stdout.write(canonical_json(error_mapping("DG7_INVALID_SCENARIO", "missing explicit scenario")))
        return 2

    output = Path(args.output)
    try:
        if output.exists():
            output.unlink()
        receipt = run_reference_runtime(Path(args.work_root), scenario_id=args.scenario)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(canonical_json(receipt_to_mapping(receipt)), encoding="utf-8", newline="\n")
        return 0
    except DG7RuntimeVerificationError as exc:
        sys.stdout.write(canonical_json(error_mapping(exc.reason_code, str(exc))))
        return 2
    except Exception:
        sys.stdout.write(canonical_json(error_mapping("DG7_INVALID_SCENARIO", "DG7 structured failure")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
