"""Source/graph-routed baseline with heuristic layout and geometric neighborhood readback."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from field_demo import read_field, write_field
from task_recall import _layout


def jsonl(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def git_tree(repo, rev):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args])
    commit = git("rev-parse", "--verify", "--end-of-options", rev + "^{commit}").decode().strip()
    tree = {}
    for row in git("ls-tree", "-rz", commit).split(b"\0"):
        if row:
            header, path = row.split(b"\t", 1)
            mode, kind, oid = header.split()
            if mode in {b"100644", b"100755"} and kind == b"blob":
                tree[path.decode("utf-8", "surrogateescape")] = oid.decode()
    return commit, tree


def arch_layout(rows, edges):
    # Prefer shared evidence, then the verified dependency between two records.
    # Saturate repeated edges so a frequently repeated import cannot dominate.
    owners = defaultdict(set)
    for row in rows:
        for ref in row["evidence"]:
            owners[ref["path"]].add(row["key"])
    weights = defaultdict(Counter)
    for keys in owners.values():
        for a in keys:
            for b in keys:
                if a != b:
                    weights[a][b] = 6
    for src, dst in edges:
        for a in owners[src]:
            for b in owners[dst]:
                if a != b:
                    weights[a][b] = max(1, weights[a][b])
                    weights[b][a] = max(1, weights[b][a])
    occupied = set()
    layout = {}
    right_edge = -3
    neighbors = ((1,0), (0,1), (-1,1), (-1,0), (0,-1), (1,-1))
    # Place narrowly scoped judgments before the broader directory records.
    for n in sorted(rows, key=lambda x: (x["kind"] != "reviewed", x["key"])):
        key = n["key"]
        votes = Counter()
        for other, weight in weights[key].items():
            if other in layout:
                q,r = layout[other]
                for dq,dr in neighbors:
                    cell = (q+dq,r+dr)
                    if cell not in occupied:
                        votes[cell] += weight
        cell = min(votes, key=lambda c:(-votes[c],c)) if votes else (right_edge+3,0)
        right_edge = max(right_edge, cell[0])
        layout[key] = cell
        occupied.add(cell)
    return layout


def build(repo, rev, records, facts, field, policy):
    if field.exists():
        raise ValueError("choose a new field directory")
    commit, tree = git_tree(repo, rev)
    rows = list(jsonl(records))
    keys = {n["key"] for n in rows}
    if not rows or len(keys) != len(rows):
        raise ValueError("supply non-empty machine records with unique keys")
    notes = []
    for n in rows:
        if n["commit"] != commit:
            raise ValueError("record commit differs from the requested tree")
        refs = n["evidence"]
        if not refs or any(tree.get(r["path"]) != r["blob"] for r in refs):
            raise ValueError(f"{n['key']}: Git evidence disagrees")
        notes.append(dict(key=n["key"], text=encoded(n), reviewed_commit=commit, status="current", evidence=refs))
    if policy == "shared":
        layout = _layout(notes)
    else:
        fact_manifest = json.loads((facts / "manifest.json").read_text(encoding="utf-8"))
        if fact_manifest["commit"] != commit:
            raise ValueError("fact graph and Git revision disagree")
        edges = set()
        for e in jsonl(facts/"edges.jsonl"):
            if e["confidence"] == "exact":
                if tree.get(e["src"]) != e["src_blob"] or tree.get(e["dst"]) != e["dst_blob"]:
                    raise ValueError("edge evidence disagrees with the requested tree")
                edges.add((e["src"],e["dst"]))
        layout = arch_layout(rows, edges)
    field.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=field.parent) as tmp:
        stage = Path(tmp)/"field"
        stage.mkdir()
        write_field(stage, dict(commit=commit, notes=notes), [(k,*c) for k,c in sorted(layout.items())],
                    decided_by="fixture", reason_text=f"Baseline {policy} heuristic selected this cell.")
        # The route index maps a file to a physical entry. Access holds the full payload.
        route = {n["key"]: {"kind":n["kind"], "paths":[r["path"] for r in n["evidence"]],
                            "digest":sha256(encoded(n).encode()).hexdigest()} for n in rows}
        (stage/"route.json").write_text(encoded(dict(commit=commit, policy=policy, records=route))+"\n", encoding="utf-8")
        stage.rename(field)
    return dict(mode="source_routed_"+policy+"_baseline", commit=commit, records=len(notes), policy=policy)


def pick(records, seeds):
    ranking = {p: len(seeds)-i for i,p in enumerate(seeds)}
    votes = {}
    for key, item in records.items():
        paths = item["paths"]
        weight = sum(ranking.get(p,0) * (2 if i==0 else 1) for i,p in enumerate(paths))
        if weight:
            votes[key] = weight/(2+len(paths)**0.5)
    return min(votes, key=lambda k:(-votes[k],k)) if votes else None


def query(repo, rev, field, batch, include_records=False):
    commit, tree = git_tree(repo, rev)
    route = json.loads((field/"route.json").read_text(encoding="utf-8"))
    if route["commit"] != commit:
        raise ValueError("field is pinned to a different commit; rebuild using current records")
    if batch.get("commit", commit) != commit:
        raise ValueError("seed batch and field revision disagree")
    results = []
    for case in batch["results"]:
        seeds = list(dict.fromkeys(case["paths"]))[:5]
        if any(p not in tree for p in seeds):
            raise ValueError("untracked seed")
        entry = pick(route["records"],seeds)
        keys, ordered, trails, payloads = [], [], [], []
        if entry is not None:
            native = read_field(field, commit, entry+"@"+commit, 3)
            if not native["recalled"] or native["recalled"][0]["statement_id"] != entry+"@"+commit:
                raise ValueError("physical entry and current binding disagree")
            for item in native["recalled"]:
                row = json.loads(item["text"])
                key = row["key"]
                refs = row["evidence"]
                if (row["commit"] != commit or item["statement_id"] != key+"@"+commit or
                    sha256(item["text"].encode()).hexdigest()!=route["records"][key]["digest"] or
                    [r["blob"]+":"+r["path"] for r in refs] != item["evidence_blobs"] or
                    any(tree.get(r["path"])!=r["blob"] for r in refs)):
                    raise ValueError("native statement, binding or Git citation mismatch")
                if include_records:
                    payloads.append(row)
                keys.append(key)
                trails.append(item["kernel_path"])
                paths = [r["path"] for r in refs]
                # Within each physically obtained record, use the source-ranker order first.
                ordered.append([p for p in seeds if p in paths]+[p for p in paths if p not in seeds])
        selected = []
        for offset in range(max(map(len,ordered),default=0)):
            for group in ordered:
                if offset < len(group) and group[offset] not in selected:
                    selected.append(group[offset])
            if len(selected)>=5:
                break
        results.append(dict(id=case["id"],query=case.get("query",""),entry=entry,keys=keys,
                            kernel_paths=trails,paths=selected[:5],status="ok" if keys else "no_match"))
        if include_records:
            results[-1]["records"] = payloads
    return dict(mode="source_routed_"+route["policy"]+"_baseline",commit=commit,results=results)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build","query"):
        p = sub.add_parser(name)
        p.add_argument("--repo",type=Path,required=True)
        p.add_argument("--field",type=Path,required=True)
        p.add_argument("--rev",default="HEAD")
        p.add_argument("--out",type=Path)
        if name=="build":
            p.add_argument("--records",type=Path,required=True)
            p.add_argument("--facts",type=Path,required=True)
            p.add_argument("--layout",choices=["shared","architecture"],default="architecture")
        else:
            p.add_argument("--seeds",type=Path,required=True)
            p.add_argument("--include-records", action="store_true")
    a=parser.parse_args(argv)
    try:
        result=(build(a.repo,a.rev,a.records,a.facts,a.field,a.layout) if a.command=="build"
                else query(a.repo,a.rev,a.field,json.loads(a.seeds.read_text(encoding="utf-8")), a.include_records))
    except (KeyError,ValueError,OSError,subprocess.CalledProcessError) as exc:
        parser.exit(2,f"{parser.prog}: {exc}\n")
    if a.out:
        a.out.write_text(encoded(result)+"\n",encoding="utf-8")
    else:
        print(encoded(result))


if __name__=="__main__":
    main()
