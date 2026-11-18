"""Select one physical entry for a repository task and recall its neighborhood."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from math import log
from pathlib import Path
import re

from field_demo import replay_field
from repo_notes import format_note, inspect_notes


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


def recall_task(repo: Path, manifest: dict, query: str, rev: str = "HEAD",
                limit: int = 3) -> dict:
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

    layout = _layout(current)
    placements = [(key, q, r) for key, (q, r) in layout.items()]
    native = replay_field(assessment, placements, layout[key], limit)
    for item in native["recalled"]:
        note_key, commit = item["statement_id"].rsplit("@", 1)
        evidence = []
        for ref in item["evidence_blobs"]:
            blob, path = ref.split(":", 1)
            evidence.append({"path": path, "blob": blob})
        result["matches"].append({
            "key": note_key, "text": item["text"], "reviewed_commit": commit,
            "evidence": evidence, "kernel_path": item["kernel_path"],
        })
    result.update(status="ok", entry=native["entry"])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--rev", default="HEAD")
    parser.add_argument("--limit", type=int, default=3, help="maximum native results, 1 to 7")
    parser.add_argument("--format", choices=("json", "view"), default="json",
                        help="full native evidence or compact notes in the same format as view")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = recall_task(args.repo, manifest, args.query, args.rev, args.limit)
    except (ValueError, OSError, RuntimeError) as error:
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
