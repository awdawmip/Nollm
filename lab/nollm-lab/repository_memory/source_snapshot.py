"""Read fixed Git source windows from an explicitly selected portable snapshot.

The snapshot preserves original files; it is an evidence source, not a memory
entry or a relationship index. Only the exact requested file is opened.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re


SCHEMA = "nollm_source_snapshot_v1"
_SHA = re.compile(r"[0-9a-f]{40}\Z")


def _source_path(path):
    if not isinstance(path, str):
        raise ValueError("source path must be a repository-relative string")
    relative = PurePosixPath(path)
    if (not path or not relative.parts or relative.is_absolute()
            or ".." in relative.parts or str(relative) != path or "\\" in path):
        raise ValueError(f"source path must be repository-relative: {path}")
    return relative


def split_reference(reference):
    """Parse the existing COMMIT:path#Lfirst-Llast source representation."""
    try:
        blob, window = reference.rsplit("#L", 1)
        commit, path = blob.split(":", 1)
        first, separator, last = window.partition("-L")
        first, last = int(first), int(last if separator else first)
    except (AttributeError, ValueError) as error:
        raise ValueError(f"invalid fixed source reference: {reference}") from error
    if not _SHA.fullmatch(commit) or not 1 <= first <= last:
        raise ValueError(f"invalid fixed source reference: {reference}")
    _source_path(path)
    return commit, path, first, last


class SourceSnapshot:
    def __init__(self, root):
        self.root = Path(root)
        self.manifest = json.loads((self.root / "snapshot.json").read_text(encoding="utf-8"))
        if self.manifest.get("schema") != SCHEMA:
            raise ValueError("unsupported source snapshot schema")
        self.repository = self.manifest.get("repository")
        self.commit = self.manifest.get("commit")
        self.files = self.manifest.get("files")
        if (not isinstance(self.repository, str) or not self.repository
                or not isinstance(self.commit, str) or not _SHA.fullmatch(self.commit)
                or not isinstance(self.files, dict)):
            raise ValueError("snapshot needs repository, full commit SHA and files mapping")
        self._opened = {}

    def revision(self, rev="HEAD"):
        if rev not in ("HEAD", self.commit):
            raise ValueError(f"snapshot contains {self.commit}; requested revision is {rev}")
        return self.commit

    def text(self, path):
        relative = _source_path(path)
        if path in self._opened:
            return self._opened[path]
        if path not in self.files:
            raise ValueError(f"source is not declared in snapshot: {path}")
        metadata = self.files[path]
        if (not isinstance(metadata, dict) or not isinstance(metadata.get("blob_sha"), str)
                or not _SHA.fullmatch(metadata["blob_sha"])
                or type(metadata.get("size")) is not int or metadata["size"] < 0):
            raise ValueError(f"source metadata needs Git blob SHA and byte size: {path}")
        data = (self.root / "files" / relative).read_bytes()
        # This is the evidence read boundary: detect an edited or incomplete
        # portable file before describing it as the pinned Git source.
        actual = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if len(data) != metadata["size"] or actual != metadata["blob_sha"]:
            raise ValueError(f"snapshot file differs from its pinned Git blob: {path}")
        text = data.decode("utf-8")
        self._opened[path] = text
        return text

    def excerpt(self, reference):
        commit, path, first, last = split_reference(reference)
        self.revision(commit)
        lines = self.text(path).splitlines()
        if last > len(lines):
            raise ValueError(f"line window outside source: {reference} ({len(lines)} lines)")
        return "\n".join([reference, *(f"{n}\t{lines[n-1]}" for n in range(first, last + 1))])

    def citations(self, citations, rev="HEAD"):
        commit = self.revision(rev)
        references = []
        for citation in citations:
            reference = f"{commit}:{citation}"
            self.excerpt(reference)
            references.append(reference)
        return references
