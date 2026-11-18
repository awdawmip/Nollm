"""Reproduce a file-byte cost model; this is not a retrieval or quality benchmark.

From a Nollm checkout containing the pinned commit:
  python lab/nollm-lab/repository_memory/evaluate_reads.py --repo .
  python lab/nollm-lab/repository_memory/evaluate_reads.py --questions-only

The question list is suitable for a *new* blind run. The full report includes
answers and gold evidence and must not be shown to a solver being evaluated.
The compact-view size is measured from the sibling tool's actual stdout,
including newlines, at the pinned revision (not a simulated renderer).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


REVISION = "314eb47490adcad22e37d6e05d2da3983e78956d"
ACCESS = "packages/nollm-access/src/nollm_access/"
STATEMENT = ACCESS + "statement.py"
STORE = ACCESS + "statement_store.py"
HANDLES = ACCESS + "handle_store.py"
RUNTIME = ACCESS + "runtime.py"
SNAPSHOT = "packages/nollm-snapshot/src/nollm_snapshot/service.py"
CASES = (
    ("q1", "How are context references represented in a statement in memory and in its canonical mapping?",
     "In memory they are a tuple of nonempty strings (empty tuple allowed). The mapping stores a list; deserialization converts it back to a tuple.", (STATEMENT,)),
    ("q2", "What happens when the same statement ID is written again, and where does a read fall back if its canonical file is absent?",
     "Identical canonical bytes are a no-op; conflicting canonical content raises FileExistsError. Reads fall back from access/statements to access/evidence and expect the legacy schema there.", (STORE,)),
    ("q3", "If a different unbound statement reuses an already bound live handle, which statement's text does subsequent normal recall try to return?",
     "Reuse adds the new ID as support without replacing the current ID. Recall resolves the current statement, and emits its text only when it matches the recalled atom payload.", (HANDLES, RUNTIME)),
    ("q4", "If conditional placement sees a different Core state digest, which status and digest does it report, and is the new statement written?",
     "It returns stale_zero_write and the digest of the currently exported Core state, with no result and no new statement write.", (RUNTIME,)),
    ("q5", "What does the snapshot clone operation return, and how is verification performed?",
     "Clone exports bytes from the source port, imports them into the target and returns those bytes. Verify compares the port's exported bytes with the expected bytes.", (SNAPSHOT,)),
    ("q6", "During conditional placement, a staged new statement's apply raises an ordinary exception. How does cleanup distinguish a new matching canonical file from an older statement or changed bytes?",
     "The runtime checks pre-existence and only calls discard_new for a new statement if supported. The file store only unlinks the matching canonical bytes; it returns false when absent and raises FileExistsError on mismatch.", (RUNTIME, STORE)),
)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def measure(repo, manifest):
    encoded = manifest.read_bytes()
    notes = json.loads(encoded)
    if notes["schema"] != "nollm_repo_notes_v1":
        raise ValueError("expected the Nollm repository-notes manifest")
    sources = {}
    for note in notes["notes"]:
        if note["reviewed_commit"] != REVISION:
            raise ValueError("this case set is defined for the pinned source revision")
        for entry in note["evidence"]:
            path = entry["path"]
            obj = git(repo, "rev-parse", f"{REVISION}:{path}").decode().strip()
            if obj != entry["blob"]:
                raise ValueError(f"manifest evidence differs from pinned Git source: {path}")
            if path not in sources:
                sources[path] = len(git(repo, "cat-file", "blob", obj))
    gold_union = {p for _, _, _, paths in CASES for p in paths}
    if set(sources) != gold_union:
        raise ValueError("manifest evidence must cover exactly the case set's five-file corpus")
    corpus = sum(sources.values())
    rows = []
    for case_id, question, answer, paths in CASES:
        rows.append(dict(id=case_id, question=question, answer_key=answer,
                         gold_paths=paths, whole_source_bytes=corpus,
                         oracle_source_bytes=sum(sources[p] for p in paths)))
    oracle_cold = sum(r["oracle_source_bytes"] for r in rows)
    view = len(subprocess.check_output([
        sys.executable, str(Path(__file__).with_name("repo_notes.py")), "view",
        "--repo", str(repo), "--rev", REVISION, "--manifest", str(manifest),
    ]))
    return dict(
        revision=REVISION,
        method="Uncompressed bytes of distinct complete Git blobs; no separators, prompts, tool envelopes, routing, model tokens, generation or latency. Note-manifest bytes include provenance and formatting. Evidence paths are an answer key, not a selector.",
        sources=sources, manifest_bytes=len(encoded), current_view_bytes=view, cases=rows,
        independent_cold_questions=dict(
            count=len(rows), whole_source_bytes=corpus * len(rows),
            oracle_source_bytes=oracle_cold,
            whole_note_manifest_bytes=len(encoded) * len(rows),
            whole_view_bytes=len(rows) * view,
            view_plus_oracle_source_bytes=len(rows) * view + oracle_cold),
        shared_session_perfect_retention=dict(
            whole_source_bytes=corpus, oracle_source_bytes=sum(sources[p] for p in gold_union),
            whole_note_manifest_bytes=len(encoded),
            whole_view_bytes=view, view_plus_oracle_source_bytes=view + sum(sources[p] for p in gold_union)),
        interpretation="The oracle is a lower bound for this whole-file evidence protocol, conditional on knowing the designated evidence. It does not measure discovery or prove a note is sufficient. Perfect retention charges each unique input once for the whole sequence; actual model prompt billing can differ.",
    )


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--repo", type=Path, default=Path("."))
    cli.add_argument("--manifest", type=Path,
                     default=Path(__file__).resolve().parent / "examples" / "nollm-notes.json")
    cli.add_argument("--questions-only", action="store_true", help="print only question IDs and prompts")
    args = cli.parse_args()
    result = ([dict(id=i, question=q) for i, q, _, _ in CASES] if args.questions_only
              else measure(args.repo, args.manifest))
    print(json.dumps(result, indent=2, ensure_ascii=False))
