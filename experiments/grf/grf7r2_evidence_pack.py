"""Canonical GRF7R2 external evidence manifest and tar.zst pack helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
from pathlib import Path
import tarfile
from typing import Iterable

from nollm.grf.json_canonical import canonical_dumps


@dataclass(frozen=True)
class EvidenceSource:
    archive_prefix: str
    root: Path


def build_manifest(sources: Iterable[EvidenceSource], generation_commands: tuple[str, ...], producing_commit: str, report_commit: str) -> dict[str, object]:
    files = []
    for source in sources:
        for path in sorted(item for item in source.root.rglob("*") if item.is_file()):
            files.append({"relative_path": f"{source.archive_prefix}/{path.relative_to(source.root).as_posix()}", "bytes": path.stat().st_size, "sha256": _sha(path)})
    if not files:
        raise ValueError("evidence pack has no source files")
    merkle = sha256(canonical_dumps(tuple(files))).hexdigest()
    return {"schema": "grf7r2_external_artifact_manifest_v1", "generation_commands": generation_commands, "files": tuple(files), "file_count": len(files), "total_bytes": sum(int(item["bytes"]) for item in files), "merkle_root_sha256": merkle, "producing_commit": producing_commit, "report_commit": report_commit}


def write_pack(pack_path: Path, manifest_path: Path, sources: Iterable[EvidenceSource]) -> None:
    import zstandard

    mapping = {source.archive_prefix: source.root for source in sources}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with pack_path.open("wb") as raw, zstandard.ZstdCompressor(level=9).stream_writer(raw) as compressed:
        with tarfile.open(fileobj=compressed, mode="w|") as archive:
            _add_bytes(archive, "manifest/GRF7R2_EXTERNAL_ARTIFACT_MANIFEST.json", manifest_path.read_bytes())
            for item in manifest["files"]:
                relative = str(item["relative_path"])
                prefix, remainder = relative.split("/", 1)
                path = mapping[prefix] / Path(remainder)
                if not path.is_file() or path.stat().st_size != item["bytes"] or _sha(path) != item["sha256"]:
                    raise ValueError(f"evidence source changed before pack creation: {relative}")
                info = archive.gettarinfo(str(path), arcname=relative)
                info.mtime = 0
                with path.open("rb") as stream:
                    archive.addfile(info, stream)


def verify_pack(pack_path: Path) -> dict[str, object]:
    import zstandard

    observed: dict[str, tuple[int, str]] = {}
    manifest = None
    with pack_path.open("rb") as raw, zstandard.ZstdDecompressor().stream_reader(raw) as decompressed:
        with tarfile.open(fileobj=decompressed, mode="r|") as archive:
            for member in archive:
                if not member.isfile():
                    continue
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError("cannot read evidence pack member")
                payload = stream.read()
                if member.name == "manifest/GRF7R2_EXTERNAL_ARTIFACT_MANIFEST.json":
                    manifest = json.loads(payload)
                else:
                    observed[member.name] = (len(payload), sha256(payload).hexdigest())
    if not isinstance(manifest, dict) or manifest.get("schema") != "grf7r2_external_artifact_manifest_v1":
        raise ValueError("evidence pack manifest is missing or invalid")
    expected = {str(item["relative_path"]): (int(item["bytes"]), str(item["sha256"])) for item in manifest["files"]}
    if observed != expected:
        raise ValueError("evidence pack member inventory or hash does not match manifest")
    return {"manifest": manifest, "pack_sha256": _sha(pack_path), "pack_bytes": pack_path.stat().st_size, "verified_at": datetime.now(timezone.utc).isoformat()}


def _add_bytes(archive: tarfile.TarFile, name: str, payload: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    info.mtime = 0
    archive.addfile(info, io.BytesIO(payload))


def _sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
