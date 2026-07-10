"""Verify GRF7R3 local-full or external-compact evidence handoff."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tarfile

from experiments.grf.grf7r2_evidence_pack import verify_pack
from experiments.grf.grf7r3_compact_evidence import verify_capsule


def _sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_bundle(bundle: Path) -> None:
    subprocess.run(["git", "bundle", "verify", str(bundle)], check=True)


def _receipt(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "nollm_grf7r3_delivery_receipt_v2":
        raise ValueError("delivery receipt schema mismatch")
    return payload


def _full(bundle: Path, pack: Path, receipt: dict[str, object]) -> None:
    _verify_bundle(bundle)
    verified = verify_pack(pack)
    if receipt.get("bundle_sha256") != _sha(bundle):
        raise ValueError("receipt does not bind bundle")
    if receipt.get("full_evidence_sha256") != verified["pack_sha256"] or receipt.get("full_evidence_bytes") != verified["pack_bytes"]:
        raise ValueError("receipt does not bind full evidence pack")
    manifest = verified["manifest"]
    if receipt.get("full_evidence_merkle_root_sha256") != manifest.get("merkle_root_sha256"):
        raise ValueError("receipt does not bind full evidence manifest")
    _recompute_gates_from_pack(pack)
    print("LOCAL_FULL_VERIFIED")


def _recompute_gates_from_pack(pack: Path) -> None:
    import zstandard

    wanted = {
        "r2/runtime/host_registry_replay_report.json": "runtime/host_registry_replay_report.json",
        "r2/real_global/negative_query_metrics.json": "real_global/negative_query_metrics.json",
        "r2/long_running/long_running_metrics.json": "long_running/long_running_metrics.json",
    }
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        found: set[str] = set()
        with pack.open("rb") as raw, zstandard.ZstdDecompressor().stream_reader(raw) as decompressed:
            with tarfile.open(fileobj=decompressed, mode="r|") as archive:
                for member in archive:
                    if member.name not in wanted or not member.isfile():
                        continue
                    stream = archive.extractfile(member)
                    if stream is None:
                        raise ValueError(f"cannot extract gate input: {member.name}")
                    target = root / wanted[member.name]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(stream.read())
                    found.add(member.name)
        if found != set(wanted):
            raise ValueError("full evidence pack is missing Gate A-C inputs")
        result = subprocess.run([sys.executable, "experiments/grf/verify_grf7r2_evidence.py", "--evidence-root", str(root), "--output", str(root / "gate.json")], capture_output=True, text=True)
        if result.returncode != 0 or "GRF7_ACCEPTED" not in result.stdout:
            raise ValueError(f"Gate A-C recomputation failed: {result.stdout}{result.stderr}")


def _compact(bundle: Path, capsule: Path, receipt: dict[str, object]) -> None:
    _verify_bundle(bundle)
    verified = verify_capsule(capsule)
    embedded = verified["receipt"]
    for key in ("actual_final_head", "bundle_sha256", "full_evidence_sha256", "full_evidence_merkle_root_sha256"):
        if receipt.get(key) != embedded.get(key):
            raise ValueError(f"compact receipt mismatch: {key}")
    if receipt.get("bundle_sha256") != _sha(bundle):
        raise ValueError("receipt does not bind bundle")
    print("EXTERNAL_COMPACT_VERIFIED")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--mode", choices=("full", "compact"), required=True)
    parser.add_argument("--full-evidence", type=Path)
    parser.add_argument("--compact-capsule", type=Path)
    args = parser.parse_args()
    try:
        receipt = _receipt(args.receipt)
        if args.mode == "full":
            if args.full_evidence is None:
                raise ValueError("--full-evidence is required in full mode")
            _full(args.bundle, args.full_evidence, receipt)
        else:
            if args.compact_capsule is None:
                raise ValueError("--compact-capsule is required in compact mode")
            _compact(args.bundle, args.compact_capsule, receipt)
        return 0
    except Exception as exc:
        print(f"GRF7_NOT_ACCEPTED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
