"""Verify proposed machine marks against a fresh extraction from a committed Git tree."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from facts import compile_tree


def rows(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


# A symbol mark asserts a declaration at an exact line, not public API visibility.
FIELDS = {
    "file": {"path", "blob"},
    "symbol": {"path","blob","line","qualname","symbol_kind"},
    "edge": {"src","src_blob","line","dst","dst_blob","rel"},
    "judgment": {"atoms","evidence"},
}


class Evidence:
    def __init__(self, directory):
        self.files = {r["path"]:r for r in rows(directory/"files.jsonl")}
        self.symbols = {(r["path"],r["line"],r["qualname"],r["kind"]):r for r in rows(directory/"symbols.jsonl")}
        self.edges = {}
        for r in rows(directory/"edges.jsonl"):
            key = r["src"],r["line"],r["dst"],r["rel"]
            if self.edges.get(key) != "exact":
                self.edges[key] = r["confidence"]

    def anchors(self, pairs):
        for path,blob in pairs:
            if not isinstance(path,str) or not isinstance(blob,str):
                return "invalid","bad_evidence_reference"
            if path not in self.files:
                return "conflict","missing_path"
            if self.files[path]["blob"]!=blob:
                return "conflict","blob_mismatch"
        return None

    def check(self, m):
        if not isinstance(m,dict):
            return "invalid","object_required"
        kind = m.get("kind")
        if not isinstance(kind,str) or kind not in FIELDS or set(m)!=(FIELDS[kind]|{"id","kind"}):
            return "invalid","unknown_or_missing_fields"
        if not isinstance(m["id"],str) or not m["id"].strip():
            return "invalid","identifier_required"
        if "line" in m and (type(m["line"]) is not int or m["line"]<1):
            return "invalid","positive_line_required"
        if kind=="judgment":
            refs, atoms = m["evidence"],m["atoms"]
            if not isinstance(refs,list) or not refs or not all(isinstance(r,dict) and set(r)=={"path","blob"} for r in refs):
                return "invalid","evidence_required"
            if not isinstance(atoms,list) or not atoms or not all(isinstance(a,list) and len(a)==3 and all(isinstance(v,str) and v for v in a) for a in atoms):
                return "invalid","triples_required"
            return self.anchors((r["path"],r["blob"]) for r in refs) or ("review_required","semantics_need_independent_evidence")
        if not all(isinstance(v,str) and v for k,v in m.items() if k!="line"):
            return "invalid","nonempty_string_required"
        if kind=="edge":
            issue=self.anchors([(m["src"],m["src_blob"]),(m["dst"],m["dst_blob"])])
            if issue:
                return issue
            support=self.edges.get((m["src"],m["line"],m["dst"],m["rel"]))
            if support=="exact":
                return "verified","source_edge"
            if support=="candidate":
                return "candidate","unresolved_edge"
            return "unsupported","edge_witness_missing"
        issue=self.anchors([(m["path"],m["blob"])])
        if issue:
            return issue
        if kind=="file":
            return "verified","git_object"
        match = self.symbols.get((m["path"],m["line"],m["qualname"],m["symbol_kind"]))
        if match is None:
            return "unsupported","declaration_witness_missing"
        if match["kind"].endswith("_candidate"):
            return "candidate","lexical_witness"
        return "verified","declaration_witness"


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--rev", default="HEAD")
    parser.add_argument("--marks", type=Path, required=True, help="JSONL of proposed marks")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--require-verified", action="store_true", help="exit 1 if any mark lacks source verification")
    a=parser.parse_args(argv)
    try:
        with TemporaryDirectory() as tmp:
            facts=Path(tmp)/"facts"
            compile_tree(a.repo,a.rev,facts)
            idx=Evidence(facts)
            commit=json.loads((facts/"manifest.json").read_bytes())["commit"]
            result=[]
            for n,mark in enumerate(rows(a.marks),1):
                state,reason=idx.check(mark)
                result.append(dict(row=n,id=mark.get("id") if isinstance(mark,dict) else None,status=state,reason=reason))
        report=dict(commit=commit,counts=dict(Counter(r["status"] for r in result)),results=result)
        data=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
        if a.out:
            a.out.write_text(data,encoding="utf-8")
        else:
            print(data,end="")
        if a.require_verified and any(r["status"]!="verified" for r in result):
            raise SystemExit(1)
    except (OSError,ValueError,subprocess.CalledProcessError) as error:
        parser.exit(2,f"{parser.prog}: {error}\n")


if __name__=="__main__":
    main()
