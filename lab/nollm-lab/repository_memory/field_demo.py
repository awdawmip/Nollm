"""Replay host-selected repository notes in a fresh native Nollm field.

The caller chooses both placement and the single recall entry. Paths, note
keys and body text never select coordinates. No model or network is called.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nollm_access import (
    AccessDecision, AccessRecallRequest, AccessRuntime, FileHandleStore,
    FileStatementStore, MemoryStatement,
)
from nollm_core import CoreRuntime, GeometryAddress, RecallBudget

from repo_notes import inspect_notes


def _cell(q: int, r: int) -> GeometryAddress:
    return GeometryAddress("default_dream_v1", "default", 0, q, r)


def run_field_demo(repo: Path, manifest: dict, placements: list[tuple[str, int, int]],
                   entry: tuple[int, int], rev: str = "HEAD") -> dict:
    """Write the chosen current notes, reopen, then recall one lateral step.

    placements contains host decisions (note key, q, r); entry is an
    independent host decision. A stale or missing source is reported before
    opening the temporary memory. This demo never opens a user's memory.
    """
    assessment = inspect_notes(repo, manifest, rev)
    result = replay_field(assessment, placements, entry)
    result["entry_selection"] = "explicit_host_choice"
    return result


def replay_field(assessment: dict, placements: list[tuple[str, int, int]],
                 entry: tuple[int, int], limit: int = 16) -> dict:
    """Materialize a checked Git snapshot, reopen it and recall from one cell."""
    with TemporaryDirectory(prefix="nollm-repository-field-") as temporary:
        root = Path(temporary)
        write_field(root, assessment, placements)
        return read_field(root, assessment["commit"], entry, limit)


def write_field(root: Path, assessment: dict, placements: list[tuple[str, int, int]]) -> None:
    """Publish checked statements and host-selected placements into a fresh workspace."""
    by_key = {note["key"]: note for note in assessment["notes"]}
    chosen = []
    for key, q, r in placements:
        if key not in by_key:
            raise ValueError(f"unknown note: {key}")
        note = by_key[key]
        if note["status"] != "current":
            raise ValueError(f"{key}: source is {note['status']} at {assessment['commit']}")
        evidence = note["evidence"]
        # A commit:path reference can be opened using git show. The blob IDs
        # also identify the exact reviewed bytes independently of a rename.
        primary = evidence[0]
        statement = MemoryStatement(
            f"{key}@{note['reviewed_commit']}", note["text"],
            f"{note['reviewed_commit']}:{primary['path']}",
            tuple(f"{item['blob']}:{item['path']}" for item in evidence),
        )
        chosen.append((statement, _cell(q, r)))
    if not chosen:
        raise ValueError("supply at least one host-selected placement")

    with CoreRuntime(root) as core, AccessRuntime(
        core, FileStatementStore(root), FileHandleStore(root)
    ) as writer:
        for statement, address in chosen:
            writer.put_statement(statement)
            writer.apply(AccessDecision(
                "host-new:" + statement.statement_id, statement.statement_id,
                "new", target_cell=address, decided_by="host",
                reason_text="Host chose a new placement in this empty repository field.",
            ))


def read_field(root: Path, commit: str, entry: tuple[int, int] | str, limit: int) -> dict:
    """Reopen an existing field. Resolve a statement entry using its native binding."""
    with CoreRuntime(root) as core, AccessRuntime(
        core, FileStatementStore(root), FileHandleStore(root)
    ) as reader:
        by_statement = isinstance(entry, str)
        if by_statement:
            address = reader.handle_store.get(entry).geometry_address
            entry = address.q, address.r
        found = reader.recall(AccessRecallRequest(
            "repository-field-recall", entry_cells=(_cell(*entry),),
            allowed_kernels=("lateral",),
            budget=RecallBudget(1, 8, 0, 1, 0, limit),
        ))
        recalled = []
        for item in found.items:
            if item.fallback_error:
                raise RuntimeError(f"native recall failed: {item.fallback_error}")
            cited = reader.statement_store.get(item.statement_id)
            recalled.append({
                "statement_id": item.statement_id,
                "text": item.evidence_utf8,
                "source": cited.source_handle,
                "evidence_blobs": list(cited.context_refs),
                "kernel_path": list(item.path),
            })
        result = {
            "source_commit": commit,
            "entry": list(entry),
            "budget_exhausted": found.budget_exhausted,
            "recalled": recalled,
        }
        if not by_statement:  # The explicit-placement demo reports field size.
            result["placed"] = core.placement_count()
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--rev", default="HEAD")
    parser.add_argument("--place", metavar=("NOTE_KEY", "Q", "R"), nargs=3,
                        action="append", required=True)
    parser.add_argument("--entry", metavar=("Q", "R"), nargs=2, type=int, required=True)
    args = parser.parse_args()
    placements = [(key, int(q), int(r)) for key, q, r in args.place]
    result = run_field_demo(args.repo, json.loads(args.manifest.read_text(encoding="utf-8")),
                            placements, tuple(args.entry), args.rev)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
