from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from experiments.grf.grf7r2_evidence_pack import verify_pack


def _sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--evidence-pack", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        subprocess.run(["git", "bundle", "verify", str(args.bundle)], check=True)
        verified = verify_pack(args.evidence_pack)
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        if receipt.get("bundle_sha256") != _sha(args.bundle) or receipt.get("evidence_pack_sha256") != verified["pack_sha256"]:
            raise ValueError("delivery receipt does not bind bundle and evidence pack bytes")
        manifest = verified["manifest"]
        if receipt.get("external_manifest_sha256") != sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest():
            raise ValueError("delivery receipt does not bind external manifest")
        print("GRF7_ACCEPTED")
        return 0
    except Exception as exc:
        print(f"GRF7_NOT_ACCEPTED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
