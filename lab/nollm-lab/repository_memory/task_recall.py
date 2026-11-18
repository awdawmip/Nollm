"""Select one physical entry for a repository task and recall its neighborhood."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import errno
from hashlib import sha256
import json
from math import log
import os
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from threading import RLock

from field_demo import read_field, write_field
from repo_notes import _git, format_note, inspect_notes, read_manifest


# Ignore common prompt glue and generic path components when choosing an entry.
_STOP = set("""
a an and are as at be by can do does for from how if in is it of on or should
that the their then these this to was what when where which with would you
src packages test tests py
""".split())
_CJK = r"[\u3400-\u4dbf\u4e00-\u9fff]"
_WORD = re.compile(rf"{_CJK}+|(?:(?!{_CJK})[^\W_])+")


def _terms(value: str) -> set[str]:
    words = set()
    for token in _WORD.findall(value):
        if re.fullmatch(_CJK + "+", token):
            if len(token) == 1:
                words.add(token)
            else:
                words.update(token[i:i + 2] for i in range(len(token) - 1))
        else:
            words.add(token.casefold())
            parts = re.sub(r"([A-Z])([A-Z][a-z])", r"\1 \2", token)
            parts = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", parts)
            words.update(parts.casefold().split())
    return words - _STOP


def _entry(notes: list[dict], query: str) -> tuple[str | None, list[str]]:
    """Rank on exact normalized terms. Keys, source paths and prose weigh 3:2:1."""
    wanted = _terms(query)
    frequencies = Counter()
    candidates = {}
    for note in notes:
        hits = {}
        fields = (note["text"], " ".join(ref["path"] for ref in note["evidence"]), note["key"])
        for weight, field in enumerate(fields, start=1):
            for term in _terms(field) & wanted:
                hits[term] = weight
        if hits:
            candidates[note["key"]] = hits
            frequencies.update(hits.keys())
    if not candidates:
        return None, []

    def order(key):
        # Sort terms before summing for repeatability across Python hash seeds.
        hits = candidates[key]
        score = sum(hits[t] * (1 + log((len(notes) + 1) / (frequencies[t] + 1)))
                    for t in sorted(hits))
        return -score, key

    winner = min(candidates, key=order)
    return winner, sorted(candidates[winner])


def _layout(notes: list[dict]) -> dict[str, tuple[int, int]]:
    """Place each key near notes citing the same paths, independently of the query."""
    by_path = defaultdict(list)
    occupied = set()
    layout = {}
    right_edge = -3
    for note in sorted(notes, key=lambda item: item["key"]):
        votes = Counter()
        for ref in note["evidence"]:
            for q, r in by_path[ref["path"]]:
                for dq, dr in ((-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)):
                    neighbor = q + dq, r + dr
                    if neighbor not in occupied:
                        votes[neighbor] += 1
        if votes:
            cell = min(votes, key=lambda c: (-votes[c], c))
        else:
            cell = right_edge + 3, 0
        layout[note["key"]] = cell
        right_edge = max(right_edge, cell[0])
        occupied.add(cell)
        for ref in note["evidence"]:
            by_path[ref["path"]].append(cell)
    return layout


# The native single-owner contract is process-local. Published fields are
# opened only for recall; independent CLI processes can read them concurrently.
_READER_LOCK = RLock()
_CACHE_VERSION = "fields-v1"


def _build_field(root: Path, assessment: dict, notes: list[dict]) -> None:
    layout = _layout(notes)
    write_field(root, assessment, [(key, q, r) for key, (q, r) in layout.items()])


def _cached_field(repo: Path, assessment: dict, notes: list[dict]) -> Path:
    git_dir = Path(os.fsdecode(_git(repo, "rev-parse", "--absolute-git-dir").removesuffix(b"\n")))
    # The directory version identifies layout and native serialization policy.
    # Reuse across commits if every statement and its reviewed evidence survives.
    rows = [(n["key"], n["text"], n["reviewed_commit"],
             [(r["path"], r["blob"]) for r in n["evidence"]])
            for n in sorted(notes, key=lambda n: n["key"])]
    canonical = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    parent = git_dir / "nollm-repository-memory" / _CACHE_VERSION
    target = parent / sha256(canonical).hexdigest()
    if target.is_dir():
        return target
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with TemporaryDirectory(dir=parent, prefix=".build-") as temporary:
        stage = Path(temporary)
        _build_field(stage, assessment, notes)
        try:
            stage.rename(target)
        except OSError as error:
            # Another process completed the same immutable field first.
            if error.errno not in (errno.EEXIST, errno.ENOTEMPTY) or not target.is_dir():
                raise
    return target


def _recall_native(repo: Path, assessment: dict, notes: list[dict], statement_id: str,
                   limit: int, cache: bool) -> dict:
    if cache:
        try:
            field = _cached_field(repo, assessment, notes)
            with _READER_LOCK:
                return read_field(field, assessment["commit"], statement_id, limit)
        except OSError as error:
            if error.errno not in (errno.EPERM, errno.EACCES, errno.EROFS):
                raise
    with TemporaryDirectory(prefix="nollm-repository-field-") as temporary:
        root = Path(temporary)
        _build_field(root, assessment, notes)
        return read_field(root, assessment["commit"], statement_id, limit)


def recall_task(repo: Path, manifest: dict, query: str, rev: str = "HEAD",
                limit: int = 3, *, cache: bool = True) -> dict:
    """Return current native statements and Git citations from one selected entry."""
    if type(limit) is not int or not 1 <= limit <= 7:
        raise ValueError("limit must be an integer between 1 and 7")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be non-empty")
    assessment = inspect_notes(repo, manifest, rev)
    current = [n for n in assessment["notes"] if n["status"] == "current"]
    key, terms = _entry(current, query)
    result = {"status": "no_match", "commit": assessment["commit"], "entry_key": key,
              "entry": None, "matched_terms": terms, "matches": []}
    if key is None:
        return result

    by_key = {note["key"]: note for note in current}
    entry_id = f"{key}@{by_key[key]['reviewed_commit']}"
    native = _recall_native(repo, assessment, current, entry_id, limit, cache)
    if not native["recalled"] or native["recalled"][0]["statement_id"] != entry_id:
        raise ValueError("native field disagrees with verified manifest; retry with --no-cache")
    for item in native["recalled"]:
        note_key, commit = item["statement_id"].rsplit("@", 1)
        note = by_key.get(note_key)
        if note is None or commit != note["reviewed_commit"] or item["text"] != note["text"]:
            raise ValueError("native statement disagrees with verified manifest; retry with --no-cache")
        evidence = []
        for saved, ref in zip(item["evidence_blobs"], note["evidence"], strict=True):
            if saved != f"{ref['blob']}:{ref['path']}":
                raise ValueError("native citation disagrees with verified manifest; retry with --no-cache")
            evidence.append({"path": ref["path"], "blob": ref["blob"]})
        result["matches"].append({
            "key": note_key, "text": item["text"], "reviewed_commit": commit,
            "evidence": evidence, "kernel_path": item["kernel_path"],
        })
    result.update(status="ok", entry=native["entry"])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, help="default: .nollm/repository-notes.json at the Git root")
    parser.add_argument("--query", required=True)
    parser.add_argument("--rev", default="HEAD")
    parser.add_argument("--limit", type=int, default=3, help="maximum native results, 1 to 7")
    parser.add_argument("--no-cache", action="store_true",
                        help="build in a temporary directory instead of reusing the native Git-local field")
    parser.add_argument("--format", choices=("json", "view"), default="json",
                        help="full native evidence or compact notes in the same format as view")
    args = parser.parse_args(argv)
    try:
        manifest = read_manifest(args.repo, args.manifest)
        result = recall_task(args.repo, manifest, args.query, args.rev, args.limit, cache=not args.no_cache)
    except (KeyError, ValueError, OSError, RuntimeError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")
    if args.format == "view":
        for match in result["matches"]:
            print(format_note(match))
        if result["status"] == "no_match":
            print("no_match")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
