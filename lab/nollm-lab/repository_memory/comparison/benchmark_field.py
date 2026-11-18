"""Compare end-to-end native recall from the skill CLI at the last release and current checkout."""
from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import io
import json
from math import ceil
from pathlib import Path
import platform
import pstats
import shutil
import statistics
import subprocess
import sys
import tarfile
import tempfile
from time import perf_counter_ns

PREVIOUS = "b2680557d8452b8ab66179d1626fda4c86407976"
SOURCE = "314eb47490adcad22e37d6e05d2da3983e78956d"
LAB = Path("lab/nollm-lab/repository_memory")
CLI = LAB / "skills/nollm-repository-memory/scripts/memory.py"
QUERIES = ["binding.current", "statement.retry", "snapshot.scope", "recall.evidence"]
PACKAGES = ["packages/nollm-core/src", "packages/nollm-access/src"]
# Only used by the freshness probe in the disposable checkout.
AUXILIARY = "packages/nollm-access/src/nollm_access/handle_store.py"


def git(repo, *args):
    return subprocess.check_output(["git", "-C", repo, *args])


def clone(source, target):
    git(source, "clone", "-q", "--shared", "--no-checkout", str(source), str(target))
    git(target, "checkout", "-q", "--detach", SOURCE)


def build_manifest(target, small, size):
    data = json.loads(small.read_bytes())
    rows = data["notes"]
    existing = {note["evidence"][0]["path"] for note in rows}
    for path in sorted((target / "packages").glob("*/src/*/*.py")):
        if len(rows) == size:
            break
        name = path.relative_to(target).as_posix()
        if path.name == "__init__.py" or name in existing:
            continue
        definitions = [node.name for node in ast.parse(path.read_bytes()).body
                       if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and not node.name.startswith("_")]
        if not definitions:
            continue
        rows.append({
            "key": f"structure.{path.parent.name}.{path.stem}",
            "text": f"{path.parent.name}.{path.stem} defines {', '.join(definitions[:4])}.",
            "reviewed_commit": SOURCE,
            "evidence": [{"path": name, "blob": git(target, "rev-parse", f"{SOURCE}:{name}").decode().strip()}],
        })
    if len(rows) != size:
        raise ValueError(f"could prepare only {len(rows)} notes for requested {size}")
    return data


def summarize(samples):
    return {"n": len(samples), "median_ms": round(statistics.median(samples), 2),
            "p95_ms": round(sorted(samples)[ceil(0.95 * len(samples)) - 1], 2),
            "samples_ms": [round(s, 3) for s in samples]}


def invoke(python_args, script, repo, manifest, query, rev="HEAD"):
    command = [sys.executable, *python_args, script, "recall", "--repo", repo, "--manifest", manifest,
               "--rev", rev, "--query", query, "--format", "json"]
    start = perf_counter_ns()
    output = subprocess.check_output(command)
    return (perf_counter_ns() - start) / 1_000_000, output


def profile(python_args, script, repo, manifest, folder, query):
    path = folder / "profile.pstats"
    invoke([*python_args, "-m", "cProfile", "-o", str(path)], script, repo, manifest, query)
    stats = pstats.Stats(str(path))
    # Nested cumulative times may overlap. List measured calls at the lab, Git and native boundaries.
    names = {"inspect_notes", "_entry", "_layout", "replay_field", "_git", "recall",
             "put_statement", "apply", "write_field", "read_field", "_read_field", "_write_field"}
    result = []
    for (filename, line, function), (_, calls, _, cumulative, _) in stats.stats.items():
        if function == "_find_and_load" and "importlib" in filename:
            result.append({"function": "importlib._find_and_load", "calls": calls,
                           "cumulative_ms": round(cumulative * 1000, 2)})
        elif function in names and "nollm" in filename.lower():
            result.append({"function": f"{Path(filename).name}:{function}", "calls": calls,
                           "cumulative_ms": round(cumulative * 1000, 2)})
    return sorted(result, key=lambda row: -row["cumulative_ms"])


def checked_pair(launchers, repo, manifest, query, rev):
    responses = [invoke(args, cli, repo, manifest, query, rev)[1] for args, cli in launchers.values()]
    if responses[0] != responses[1]:
        raise AssertionError(f"freshness or historical parity differs at {rev} for {query}")
    return json.loads(responses[0])


def freshness(launchers, repo, manifest):
    query = "recall.evidence"
    before = checked_pair(launchers, repo, manifest, query, "HEAD")
    if before["entry_key"] != query:
        raise AssertionError("probe did not populate the target note")
    with (repo / AUXILIARY).open("a", encoding="utf-8") as stream:
        stream.write("\n# auxiliary evidence changed in performance fixture\n")
    git(repo, "add", "--", AUXILIARY)
    git(repo, "-c", "user.name=Benchmark", "-c", "user.email=benchmark@localhost",
        "commit", "-qm", "change only shared supporting evidence")
    changed = checked_pair(launchers, repo, manifest, query, "HEAD")
    if changed["commit"] == before["commit"] or any(row["key"] == query for row in changed["matches"]):
        raise AssertionError("stale source note remained eligible")
    restored = checked_pair(launchers, repo, manifest, query, SOURCE)
    if restored != before:
        raise AssertionError("historical read failed to reproduce original evidence")
    return {"before_entry": before["entry_key"], "changed_entry": changed["entry_key"],
            "stale_key_absent": True, "historical_response_identical": True}


def benchmark(repo, temp, sizes, rounds):
    old = temp / "previous"
    old.mkdir()
    archived = git(repo, "archive", PREVIOUS, str(LAB), *PACKAGES)
    with tarfile.open(fileobj=io.BytesIO(archived)) as tar:
        tar.extractall(old, filter="data")
    # Freeze the candidate CLI and its package dependencies, including local changes.
    current = temp / "candidate"
    scripts = [CLI, LAB / "task_recall.py", LAB / "field_demo.py", LAB / "repo_notes.py"]
    for path in PACKAGES:
        scripts.extend(p.relative_to(repo) for p in (repo / path).rglob("*.py"))
    candidate_id = sha256()
    for rel in sorted(scripts):
        dest = current / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / rel, dest)
        candidate_id.update(rel.as_posix().encode() + b"\0" + sha256(dest.read_bytes()).digest())

    launchers = {}
    for label, checkout in (("previous", old), ("current", current)):
        args = ["-X", f"pycache_prefix={temp / ('pycache-' + label)}"]
        script = checkout / CLI
        subprocess.run([sys.executable, *args, script, "recall", "--help"], stdout=subprocess.DEVNULL, check=True)
        launchers[label] = args, script

    result = {"previous": PREVIOUS, "candidate_files_sha256": candidate_id.hexdigest(),
              "target": SOURCE, "python": platform.python_version(),
              "platform": platform.platform(), "queries": QUERIES, "rounds": rounds, "sizes": {}}
    for size in sizes:
        times = {name: {"cold": [], "repeat": []} for name in launchers}
        digests = {}
        manifest = temp / f"{size}.json"
        for rep in range(rounds):
            with tempfile.TemporaryDirectory(dir=temp) as folder:
                target = Path(folder) / "repo"
                clone(repo, target)
                if rep == 0:
                    data = build_manifest(target, old / LAB / "examples/nollm-notes.json", size)
                    manifest.write_text(json.dumps(data), encoding="utf-8")
                # Each process is new. The first query has no prior native field. Subsequent
                # queries rotate over different physical entries. Alternate implementation order.
                for i in range(len(QUERIES)):
                    query = QUERIES[(rep + i) % len(QUERIES)]
                    order = list(launchers) if (rep + i) % 2 == 0 else list(reversed(launchers))
                    phase = "cold" if i == 0 else "repeat"
                    for label in order:
                        args, script = launchers[label]
                        elapsed, output = invoke(args, script, target, manifest, query)
                        times[label][phase].append(elapsed)
                        digest = sha256(output).hexdigest()
                        if digests.setdefault(query, digest) != digest:
                            raise AssertionError(f"byte parity differs at size={size} round={rep} query={query}")
                        if json.loads(output)["status"] != "ok":
                            raise AssertionError("timed query did not exercise a native read")
                if rep == rounds - 1:
                    profiles = {label: profile(args, script, target, manifest, Path(folder), QUERIES[0])
                                for label, (args, script) in launchers.items()}
                    gate = freshness(launchers, target, manifest)
        result["sizes"][size] = {
            name: {phase: summarize(samples) for phase, samples in phases.items()} for name, phases in times.items()
        }
        result["sizes"][size].update(output_sha256=digests, repeat_profile=profiles, freshness=gate)
        print(f"finished {size} notes, {rounds} isolated rounds", file=sys.stderr, flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=Path("."), type=Path)
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--sizes", nargs="+", type=int, default=[5, 40])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.rounds < 1 or any(size < 5 for size in args.sizes):
        parser.error("rounds must be positive and each corpus must have at least five notes")
    with tempfile.TemporaryDirectory(prefix="nollm-skill-speed-") as temp:
        result = benchmark(args.repo.resolve(), Path(temp), args.sizes, args.rounds)
    body = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(body, encoding="utf-8")
    else:
        print(body, end="")


if __name__ == "__main__":
    main()
