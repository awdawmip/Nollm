from __future__ import annotations

import argparse
import json
from pathlib import Path

from experiments.grf.grf7r2_evidence_pack import EvidenceSource, build_manifest, write_pack


def _source(value: str) -> EvidenceSource:
    prefix, root = value.split("=", 1)
    if not prefix or not root:
        raise argparse.ArgumentTypeError("source must be prefix=directory")
    return EvidenceSource(prefix, Path(root))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", type=_source, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--producing-commit", required=True)
    parser.add_argument("--report-commit", required=True)
    parser.add_argument("--pack", type=Path)
    args = parser.parse_args()
    sources = tuple(args.source)
    manifest = build_manifest(sources, ("python experiments/grf/run_grf7r2_host_registry_validation.py", "python experiments/grf/run_grf7r2_long_running_validation.py", "python experiments/grf/run_grf7r_real_global_workload.py"), args.producing_commit, args.report_commit)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    if args.pack is not None:
        write_pack(args.pack, args.manifest, sources)
    print(json.dumps({"manifest": str(args.manifest), "file_count": manifest["file_count"], "merkle_root_sha256": manifest["merkle_root_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
