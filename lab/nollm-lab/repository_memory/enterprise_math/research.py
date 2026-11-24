"""Enterprise Math research memory. The calling model authors text and chooses cells."""
import argparse
from itertools import islice
import json
from pathlib import Path
import sys

from nollm_access import (
    RECALL_SURFACE_BUDGET, AccessDecision, AccessRecallRequest, AccessRuntime,
    FileHandleStore, FileStatementStore, MemoryStatement,
)
from nollm_core import CoreRuntime, PhysicalFieldScope, RecallBudget

from coverage_cli import address, coords, require_field, surface
from repo_notes import _commit, _git


SAVED_FIELD = Path(__file__).resolve().parent / "field"
SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)
KERNELS = {
    "local": ("coverage_down", "coverage_up", "lateral"),
    "vertical": ("coverage_down", "coverage_up"),
}


def save(field, repo, rev, note_id, body, citations, at, revise):
    commit = _commit(repo, rev)
    return save_statement(field, note_id, body, [f"{commit}:{citation}" for citation in citations], at, revise)


def save_statement(field, note_id, body, sources, at, revise):
    """Save Host-authored understanding with already selected, pinned source references."""
    primary, *others = sources
    with CoreRuntime(field) as core, AccessRuntime(
        core, FileStatementStore(field), FileHandleStore(field)
    ) as access:
        if revise is None:
            decision = AccessDecision(note_id, note_id, "new", target_cell=address(0, *at),
                                      reason_text="Host selected this cell for a distinct proposition.")
        else:
            decision = AccessDecision(note_id, note_id, "revision_current",
                                      existing_handle=access.saved_handle(revise),
                                      reason_text=f"Host supersedes {revise} in the same proposition slot.")
            others.append(f"revises:{revise}")
        access.put_statement(MemoryStatement(note_id, body, primary, tuple(others)))
        handle = access.apply(decision)
    return {"id": note_id, "cell": coords(handle.geometry_address), "revises": revise}


def describe(field, note_id):
    statement = FileStatementStore(field).get(note_id)
    sources = [statement.source_handle]
    result = {"id": note_id, "text": statement.content_utf8, "sources": sources,
              "current": FileHandleStore(field).exists(note_id)}
    for ref in statement.context_refs:
        if ref.startswith("revises:"):
            result["revises"] = ref.removeprefix("revises:")
        else:
            sources.append(ref)
    if not result["current"]:
        result["continuation"] = _revision_continuation(field, statement)
    return result


def _revision_continuation(field, statement):
    """Locate the current native revision slot without replacing old evidence."""
    store = FileStatementStore(field)
    cache = {statement.statement_id: statement}

    def chain(note_id, stop_at=None):
        seen = set()
        while note_id not in seen:
            seen.add(note_id)
            if note_id == stop_at:
                return seen, False
            try:
                if note_id not in cache:
                    cache[note_id] = store.get(note_id)
                parents = {ref.removeprefix("revises:") for ref in cache[note_id].context_refs
                           if ref.startswith("revises:")}
            except (FileNotFoundError, TypeError, ValueError, UnicodeError):
                return seen, True
            if not parents:
                return seen, False
            if len(parents) != 1 or "" in parents:
                return seen, True
            note_id = next(iter(parents))
        return seen, True

    ancestors, incomplete = chain(statement.statement_id)
    candidates = []
    for binding in FileHandleStore(field).bindings_for_atom_ids(tuple(ancestors)):
        lineage, unresolved = chain(binding.current_statement_id, statement.statement_id)
        if statement.statement_id in lineage and not unresolved:
            candidates.append({"id": binding.current_statement_id,
                               "cell": coords(binding.handle.geometry_address)})
        else:
            incomplete = incomplete or unresolved
    status = ("incomplete" if incomplete else "ambiguous" if len(candidates) > 1
              else "unique" if candidates else "not_found")
    return {"scope": "native_revision_slot", "status": status, "candidates": candidates}


def excerpt(repo, reference):
    blob, fragment = reference.rsplit("#L", 1)
    start, _, end = fragment.partition("-L")
    first, last = int(start), int(end or start)
    lines = _git(repo, "show", blob).decode("utf-8").splitlines()
    if not 1 <= first <= last <= len(lines):
        raise ValueError(f"line window outside source: {reference} ({len(lines)} lines)")
    return "\n".join([reference, *(f"{n}\t{lines[n-1]}" for n in range(first, last + 1))])


def walk(field, choices, order, page_size, steps, limit, via):
    page = surface(field, SCOPE, order, choices, page_size, RECALL_SURFACE_BUDGET.max_calls)
    if page["kind"] != "entry":
        # The first line is the Host's cue; expand the body after choosing a cell.
        for candidate in page["candidates"]:
            candidate["previews"] = [preview.splitlines()[0] for preview in candidate["previews"]]
        return page
    entry = address(*page["entry"])
    kernels = KERNELS[via]
    with CoreRuntime(field) as core, AccessRuntime(
        core, FileStatementStore(field), FileHandleStore(field)
    ) as access:
        recall = access.recall(AccessRecallRequest(
            "em-research", (entry,), allowed_kernels=kernels,
            budget=RecallBudget(steps, 16, steps, 1, 0, limit),
        ))
    items = []
    for hit in recall.items:
        if hit.fallback_error:
            raise RuntimeError(hit.fallback_error)
        items.append({"id": hit.statement_id, "cell": coords(hit.handle.geometry_address),
                      "via": hit.path, "text": hit.evidence_utf8})
    return {**page, "kernels": kernels, "items": items, "budget_exhausted": recall.budget_exhausted}


def literal_matches(field, term):
    """Auxiliary scan of current statements. No geometry entry is selected here."""
    require_field(field)
    term = term.casefold()
    with CoreRuntime(field) as core:
        handles = tuple(handle for cell in core.occupied_cells() for handle, _ in core.atoms_at(cell))
        bindings = FileHandleStore(field).bindings_for_handles(handles)
        store = FileStatementStore(field)
        for binding in bindings:
            note = store.get(binding.current_statement_id)
            if term in note.statement_id.casefold() or term in note.content_utf8.casefold():
                yield {"id": note.statement_id, "preview": note.content_utf8.splitlines()[0]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, default=SAVED_FIELD, help="native workspace (default: shipped field)")
    commands = parser.add_subparsers(dest="op", required=True)
    browse = commands.add_parser("walk", help="observe a Surface page; selecting a physical candidate recalls its neighborhood")
    browse.add_argument("choices", nargs="*", help="successive candidate ids shown on pages, or next")
    browse.add_argument("--order", type=int, help="initial aggregation order; default: Access budget")
    browse.add_argument("--page-size", type=int, default=3, help="1 to 8 candidates per Surface page (default: 3)")
    browse.add_argument("--steps", type=int, default=1, help="kernel steps from the selected physical entry (default: 1)")
    browse.add_argument("--limit", type=int, default=5, help="maximum returned statements after traversal (default: 5)")
    browse.add_argument("--via", choices=KERNELS, default="local")
    search = commands.add_parser("find", help="case-insensitive literal in current IDs or bodies (auxiliary)")
    search.add_argument("term")
    search.add_argument("--limit", type=int, default=5)
    show = commands.add_parser("show", help="open an exact statement version and its ordered source windows")
    show.add_argument("id")
    source = commands.add_parser("source", help="expand an EM Git window with original line numbers")
    origin = source.add_mutually_exclusive_group(required=True)
    origin.add_argument("--id", help="use this saved version and its pinned source")
    origin.add_argument("--at", help="read PATH#Lfirst-Llast directly for formation")
    source.add_argument("--number", type=int, default=1, help="1-based source number for --id")
    write = commands.add_parser("save", help="read a model-authored statement from stdin")
    write.add_argument("id", help="new, immutable statement version ID")
    placement = write.add_mutually_exclusive_group(required=True)
    placement.add_argument("--at", type=int, nargs=2, metavar=("Q", "R"), help="host-selected physical layer-zero cell")
    placement.add_argument("--revise", help="ID of the current version to supersede in place")
    write.add_argument("--cite", action="append", required=True, help="PATH#Lfirst-Llast (repeatable)")
    for command in (source, write):
        command.add_argument("--repo", type=Path, required=True, help="Enterprise Math Git checkout")
        command.add_argument("--rev", default="HEAD", help="EM revision for a new citation or direct --at window")

    args = parser.parse_args()
    if args.op == "save":
        result = save(args.field, args.repo, args.rev, args.id, sys.stdin.read().strip(),
                      args.cite, args.at, args.revise)
    elif args.op == "show":
        result = describe(args.field, args.id)
    elif args.op == "source":
        if args.id is None:
            reference = f"{_commit(args.repo, args.rev)}:{args.at}"
        else:
            sources = describe(args.field, args.id)["sources"]
            if not 1 <= args.number <= len(sources):
                raise IndexError(f"choose source 1..{len(sources)}")
            reference = sources[args.number - 1]
        print(excerpt(args.repo, reference))
        return
    elif args.op == "walk":
        result = walk(args.field, args.choices, args.order, args.page_size,
                      args.steps, args.limit, args.via)
    else:
        result = list(islice(literal_matches(args.field, args.term), args.limit))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
