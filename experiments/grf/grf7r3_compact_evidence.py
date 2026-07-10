"""GRF7R3 compact-audit manifest, sampler, and archive verification helpers."""

from __future__ import annotations

from dataclasses import dataclass
import gzip
from hashlib import sha256
import io
import json
from pathlib import Path
import tarfile
from typing import Iterable

from nollm.grf.json_canonical import canonical_dumps


SAMPLE_SEED = 7007010


@dataclass(frozen=True)
class EvidenceSource:
    prefix: str
    root: Path


def sha_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(sources: Iterable[EvidenceSource], *, producing_commit: str, report_commit: str) -> dict[str, object]:
    files = []
    partitions = []
    for source in sources:
        for path in sorted(item for item in source.root.rglob("*") if item.is_file()):
            relative = f"{source.prefix}/{path.relative_to(source.root).as_posix()}"
            item: dict[str, object] = {"relative_path": relative, "bytes": path.stat().st_size, "sha256": sha_file(path)}
            if path.suffix == ".jsonl":
                records = _line_records(path)
                item.update(_record_metadata(records))
            if "/partitions/" in f"/{relative}":
                partition_id = path.stem.replace("_placement.bin", "")
                item["partition_id"] = partition_id
                partitions.append({"partition_id": partition_id, "relative_path": relative, "sha256": item["sha256"]})
            files.append(item)
    if not files:
        raise ValueError("evidence sources are empty")
    partition_merkle = sha256(canonical_dumps(tuple(partitions))).hexdigest()
    return {
        "schema": "grf7r3_external_artifact_manifest_v1",
        "sample_seed": SAMPLE_SEED,
        "files": tuple(files),
        "file_count": len(files),
        "total_bytes": sum(int(item["bytes"]) for item in files),
        "merkle_root_sha256": sha256(canonical_dumps(tuple(files))).hexdigest(),
        "partition_count": len(partitions),
        "partition_merkle_root": partition_merkle,
        "partitions": tuple(partitions),
        "producing_commit": producing_commit,
        "report_commit": report_commit,
    }


def write_capsule(capsule_path: Path, manifest_path: Path, receipt_path: Path, report_paths: Iterable[Path], sources: Iterable[EvidenceSource]) -> None:
    import zstandard

    samples = _build_samples(tuple(sources))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with capsule_path.open("wb") as raw, zstandard.ZstdCompressor(level=9).stream_writer(raw) as compressed:
        with tarfile.open(fileobj=compressed, mode="w|") as archive:
            _add(archive, "manifest/GRF7R3_EXTERNAL_ARTIFACT_MANIFEST.json", manifest_path.read_bytes())
            _add(archive, "receipt/NOLLM_GRF7R3_DELIVERY_RECEIPT.json", receipt_path.read_bytes())
            _add(archive, "samples/GRF7R3_RAW_EVIDENCE_SAMPLES.json", canonical_dumps(samples))
            for report in sorted(report_paths):
                _add(archive, f"reports/{report.name}", report.read_bytes())
            _add(archive, "meta/CAPSULE_CONTENTS.json", canonical_dumps({
                "schema": "grf7r3_compact_capsule_v1", "manifest_merkle_root": manifest["merkle_root_sha256"],
                "sample_seed": SAMPLE_SEED, "external_review_scope": "compact_audit_capsule_not_complete_raw_evidence",
            }))


def verify_capsule(capsule_path: Path) -> dict[str, object]:
    import zstandard

    entries: dict[str, bytes] = {}
    with capsule_path.open("rb") as raw, zstandard.ZstdDecompressor().stream_reader(raw) as decompressed:
        with tarfile.open(fileobj=decompressed, mode="r|") as archive:
            for member in archive:
                if member.isfile():
                    stream = archive.extractfile(member)
                    if stream is None:
                        raise ValueError("cannot read capsule member")
                    entries[member.name] = stream.read()
    manifest = _json(entries, "manifest/GRF7R3_EXTERNAL_ARTIFACT_MANIFEST.json")
    receipt = _json(entries, "receipt/NOLLM_GRF7R3_DELIVERY_RECEIPT.json")
    samples = _json(entries, "samples/GRF7R3_RAW_EVIDENCE_SAMPLES.json")
    contents = _json(entries, "meta/CAPSULE_CONTENTS.json")
    if manifest.get("schema") != "grf7r3_external_artifact_manifest_v1":
        raise ValueError("invalid GRF7R3 manifest")
    if receipt.get("schema") != "nollm_grf7r3_delivery_receipt_v2":
        raise ValueError("invalid GRF7R3 delivery receipt")
    if contents.get("manifest_merkle_root") != manifest.get("merkle_root_sha256"):
        raise ValueError("capsule manifest merkle root mismatch")
    _verify_samples(manifest, samples)
    return {"manifest": manifest, "receipt": receipt, "sample_groups": len(samples["groups"]), "capsule_sha256": sha_file(capsule_path), "capsule_bytes": capsule_path.stat().st_size}


def _build_samples(sources: tuple[EvidenceSource, ...]) -> dict[str, object]:
    groups = []
    for source in sources:
        for path in sorted(item for item in source.root.rglob("*") if item.is_file()):
            relative = f"{source.prefix}/{path.relative_to(source.root).as_posix()}"
            if path.suffix == ".jsonl":
                records = _line_records(path)
                minimum = 2000 if path.stat().st_size >= 10 * 1024 * 1024 else 1000 if path.name == "query_ledger.jsonl" else 0
                selected = _select(records, minimum)
                if selected:
                    groups.append(_sample_group(relative, selected))
            elif "/partitions/" in f"/{relative}" and path.suffix == ".gz":
                records = _gzip_lines(path, 10)
                groups.append(_sample_group(relative, records))
    return {"schema": "grf7r3_raw_samples_v1", "sample_seed": SAMPLE_SEED, "groups": tuple(groups)}


def _line_records(path: Path) -> list[bytes]:
    with path.open("rb") as stream:
        return [line.rstrip(b"\r\n") for line in stream if line.strip()]


def _gzip_lines(path: Path, limit: int) -> list[bytes]:
    with gzip.open(path, "rb") as stream:
        records = []
        for _ in range(limit):
            line = stream.readline()
            if not line:
                break
            records.append(line.rstrip(b"\r\n"))
        return records


def _select(records: list[bytes], minimum: int) -> list[tuple[int, bytes]]:
    if not records:
        return []
    ids = set(range(min(100, len(records)))) | set(range(max(0, len(records) - 100), len(records)))
    target = max(minimum, 0)
    if target:
        step = max(1, len(records) // target)
        ids.update(range(SAMPLE_SEED % step, len(records), step))
    for index, record in enumerate(records):
        if b'"response_ok":false' in record or b'"forbidden_bridge_hit":false' in record or b'"maintenance":true' in record:
            ids.add(index)
    return [(index, records[index]) for index in sorted(ids)]


def _sample_group(relative_path: str, records: list[tuple[int, bytes]] | list[bytes]) -> dict[str, object]:
    normalized = [(index, item) for index, item in enumerate(records)] if records and isinstance(records[0], bytes) else records
    assert isinstance(normalized, list)
    entries = tuple({"record_id": index, "sha256": sha256(item).hexdigest(), "record": item.decode("utf-8", errors="replace")} for index, item in normalized)
    return {"relative_path": relative_path, "sample_record_ids": tuple(item["record_id"] for item in entries), "sample_digest": sha256(canonical_dumps(entries)).hexdigest(), "records": entries}


def _record_metadata(records: list[bytes]) -> dict[str, object]:
    selected = _select(records, 0)
    entries = tuple({"record_id": index, "sha256": sha256(item).hexdigest()} for index, item in selected)
    return {"record_count": len(records), "first_record_digest": sha256(records[0]).hexdigest() if records else None, "last_record_digest": sha256(records[-1]).hexdigest() if records else None, "sample_seed": SAMPLE_SEED, "sample_record_ids": tuple(item["record_id"] for item in entries), "sample_digest": sha256(canonical_dumps(entries)).hexdigest()}


def _verify_samples(manifest: dict[str, object], samples: dict[str, object]) -> None:
    by_path = {str(item["relative_path"]): item for item in manifest["files"]}
    for group in samples.get("groups", ()):  # type: ignore[union-attr]
        path = str(group["relative_path"])
        if path not in by_path:
            raise ValueError(f"sample has no manifest entry: {path}")
        records = tuple(group["records"])
        digest = sha256(canonical_dumps(records)).hexdigest()
        if digest != group["sample_digest"]:
            raise ValueError(f"sample digest mismatch: {path}")


def _json(entries: dict[str, bytes], name: str) -> dict[str, object]:
    if name not in entries:
        raise ValueError(f"capsule missing {name}")
    return json.loads(entries[name])


def _add(archive: tarfile.TarFile, name: str, payload: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    info.mtime = 0
    archive.addfile(info, io.BytesIO(payload))
