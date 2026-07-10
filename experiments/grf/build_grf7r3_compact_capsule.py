from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grf.grf7r3_compact_evidence import EvidenceSource, build_manifest, write_capsule


def _source(value: str) -> EvidenceSource:
    prefix, root = value.split("=", 1)
    return EvidenceSource(prefix, Path(root))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", type=_source, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--report", action="append", type=Path, default=[])
    parser.add_argument("--capsule", type=Path)
    parser.add_argument("--producing-commit", required=True)
    parser.add_argument("--report-commit", required=True)
    args = parser.parse_args()
    manifest = build_manifest(tuple(args.source), producing_commit=args.producing_commit, report_commit=args.report_commit)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    if args.capsule is not None:
        if args.receipt is None:
            raise ValueError("--receipt is required when --capsule is used")
        write_capsule(args.capsule, args.manifest, args.receipt, tuple(args.report), tuple(args.source))
    print(json.dumps({"manifest": str(args.manifest), "file_count": manifest["file_count"], "merkle_root_sha256": manifest["merkle_root_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
