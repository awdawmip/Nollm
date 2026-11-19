"""Compile typed repository-memory records from a Git tree and an authored Nollm manifest."""
import argparse
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import warnings


RECORD_SCHEMA = "nollm.machine-record/v1"
TOKEN = re.compile(r"[A-Za-z0-9_./:+><=-]+\Z")
ID = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\Z", re.ASCII)
LEGACY_IMPORT = re.compile(r"([\w.]+) 第 ([0-9]+) 行导入 ([\w.]+)")
PREDICATE = re.compile(r"[a-z][a-z0-9_]*\Z")


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def sha(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), "--literal-pathspecs", *args])


def resolve(repo, rev):
    return git(repo, "rev-parse", "--verify", "--end-of-options", rev + "^{commit}").decode().strip()


def git_tree(repo, commit):
    result = {}
    for row in git(repo, "ls-tree", "-rz", "--full-tree", commit).split(b"\0"):
        if row:
            header, raw_path = row.split(b"\t", 1)
            mode, kind, oid = header.split()
            if mode in (b"100644", b"100755") and kind == b"blob":
                result[os.fsdecode(raw_path)] = oid.decode()
    return result


def source_type(path):
    p = PurePosixPath(path)
    if "tests" in p.parts or p.name.startswith("test_"):
        return "test"
    if p.name in {"CMakeLists.txt", "Makefile", "pyproject.toml", "setup.py"}:
        return "build"
    return p.suffix.lstrip(".").lower() or "file"


class Source:
    def __init__(self, repo):
        self.repo = repo
        self.trees = {}
        self.modules = {}

    def tree(self, commit):
        if commit not in self.trees:
            self.trees[commit] = git_tree(self.repo, commit)
        return self.trees[commit]

    def module(self, path, oid):
        if oid not in self.modules:
            raw = git(self.repo, "cat-file", "blob", oid)
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    module = ast.parse(raw, filename=path)
            except (SyntaxError, ValueError):
                module = None
            self.modules[oid] = module
        return self.modules[oid]


def resolve_path(module, evidence):
    suffix = module.replace(".", "/")
    options = [suffix + ".py", suffix + "/__init__.py"]
    matches = [ref["path"] for ref in evidence if any(
        ref["path"] == opt or ref["path"].endswith("/" + opt) for opt in options)]
    if len(matches) != 1:
        raise ValueError(f"module {module!r} has {len(matches)} matching evidence paths")
    return matches[0]


def import_targets(node, src_mod, package_init):
    if isinstance(node, ast.Import):
        return {alias.name for alias in node.names}
    if not isinstance(node, ast.ImportFrom):
        return set()
    base = node.module or ""
    if node.level:
        parts = src_mod.split(".")
        if not package_init:
            parts.pop()
        if node.level > len(parts):
            return set()
        prefix = ".".join(parts[:len(parts) + 1 - node.level])
        base = ".".join(part for part in [prefix, base] if part)
    return {base, *(f"{base}.{alias.name}" for alias in node.names)}


def import_group(note, evidence, source, explicit):
    if explicit is None:
        items = [(frm, int(line), to) for frm, line, to in LEGACY_IMPORT.findall(note["text"])]
    else:
        items = [(s["source_module"], s["line"], s["target_module"]) for s in explicit]
    if not items:
        raise ValueError(f"{note['key']}: supply machine import sites with --imports")
    lookup = {r["path"]: r["blob"] for r in evidence}
    sites, atoms = [], []
    for frm, line, to in items:
        if not isinstance(line, int) or line < 1:
            raise ValueError("invalid import site line")
        src, dest = resolve_path(frm, evidence), resolve_path(to, evidence)
        mod = source.module(src, lookup[src])
        if mod is None or not any(getattr(node, "lineno", 0) == line and
                to in import_targets(node, frm, src.endswith("/__init__.py")) for node in ast.walk(mod)):
            raise ValueError(f"{note['key']}: no matching static import {src}:{line} -> {to}")
        sites.append({"source":src, "line":line, "target":dest})
        atoms.append([frm, "imports", to])
    return {"kind":"import_group", "provenance":"git_ast_import", "atoms":atoms, "import_sites":sites}


def declarations(module):
    result = []
    def visit(node, owners):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                names = owners + (child.name,)
                result.append((".".join(names), child.name, child.lineno))
                visit(child, names)
            else:
                visit(child, owners)
    visit(module, ())
    return result


def semantic(note, evidence, claims, source):
    key = note["key"]
    if key not in claims:
        raise ValueError(f"{key}: no reviewed machine projection supplied")
    supplied = claims[key]
    if supplied["legacy_sha256"] != sha(note):
        raise ValueError(f"{key}: reviewed projection does not bind the complete legacy note")
    atoms = supplied["atoms"]
    if not isinstance(atoms, list) or not atoms:
        raise ValueError(f"{key}: expected at least one reviewed atom")
    for atom in atoms:
        if (not isinstance(atom, list) or len(atom) != 3 or
                not all(isinstance(s, str) and TOKEN.fullmatch(s) for s in atom)
                or not PREDICATE.fullmatch(atom[1])):
            raise ValueError(f"{key}: invalid reviewed relation")
    # A matched declaration establishes only the source spelling and location.
    terms = {token for subj, _, obj in atoms for value in (subj,obj)
             for token in re.split(r"[+/>:]",value) if ID.fullmatch(token)}
    anchors = []
    for ref in evidence:
        if ref["path"].endswith(".py"):
            mod = source.module(ref["path"], ref["blob"])
            if mod is not None:
                for symbol, name, line in declarations(mod):
                    if symbol in terms or name in terms:
                        anchors.append({"symbol":symbol,"line":line,"path":ref["path"]})
    return {"kind":"reviewed", "provenance":"reviewed_projection", "atoms":atoms,
            "symbol_anchors":anchors}


def convert(repo, rev, manifest, claims, imports):
    if manifest.get("schema") != "nollm_repo_notes_v1":
        raise ValueError("unsupported Nollm manifest schema")
    notes = manifest["notes"]
    keys = [n["key"] for n in notes]
    if len(keys) != len(set(keys)) or not all(isinstance(k,str) and k for k in keys):
        raise ValueError("duplicate or empty note key")
    human = {k for k in keys if not k.startswith(("tree.","imports."))}
    if set(claims) != human:
        raise ValueError(f"authored claim keys differ: missing={sorted(human-set(claims))}; extra={sorted(set(claims)-human)}")
    if set(imports) - {k for k in keys if k.startswith("imports.")}:
        raise ValueError("extra import-site keys")
    source = Source(repo)
    snapshot = resolve(repo, rev)
    current = source.tree(snapshot)
    reviewed_trees = {}
    for note in sorted(notes, key=lambda n: n["key"]):
        key, reviewed = note["key"], note["reviewed_commit"]
        if reviewed not in reviewed_trees:
            if resolve(repo, reviewed) != reviewed:
                raise ValueError(f"{key}: reviewed_commit must be a full commit ID")
            reviewed_trees[reviewed] = source.tree(reviewed)
        evidence = []
        for idx, ref in enumerate(note["evidence"]):
            path, oid = ref["path"], ref["blob"]
            if reviewed_trees[reviewed].get(path) != oid or current.get(path) != oid:
                raise ValueError(f"{key}: stale or missing Git evidence: {path}")
            evidence.append({"role":"support" if idx else "primary","path":path,"blob":oid,"type":source_type(path)})
        paths = [e["path"] for e in evidence]
        if not paths or len(set(paths)) != len(paths):
            raise ValueError(f"{key}: empty or duplicated evidence paths")
        if key.startswith("tree."):
            parent = os.path.commonpath([str(PurePosixPath(p).parent) for p in paths]) or "."
            counts = Counter(e["type"] for e in evidence)
            body = {"kind":"file_group", "provenance":"git_tree_membership",
                    "atoms":[[key,"groups_paths_under",parent], [key,"member_count",str(len(paths))]],
                    "type_counts":dict(sorted(counts.items()))}
        elif key.startswith("imports."):
            body = import_group(note, evidence, source, imports.get(key))
        else:
            body = semantic(note, evidence, claims, source)
        yield dict(schema=RECORD_SCHEMA, key=key, commit=snapshot, reviewed_commit=reviewed, legacy_sha256=sha(note),
                   evidence=evidence, **body)


def compile_records(repo, rev, manifest, claims, imports, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = Counter()
    stage = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as stream:
            stage = Path(stream.name)
            for row in convert(repo, rev, manifest, claims, imports):
                stream.write(canonical(row) + b"\n")
                count[row["kind"]] += 1
        stage.replace(output)
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)
    return dict(count)


def write_template(manifest, output):
    if manifest.get("schema") != "nollm_repo_notes_v1":
        raise ValueError("unsupported Nollm manifest schema")
    template = {}
    for note in manifest["notes"]:
        key = note["key"]
        if key.startswith(("imports.", "tree.")):
            continue
        if key in template:
            raise ValueError(f"duplicate reviewed key: {key}")
        template[key] = {"legacy_sha256":sha(note), "atoms":[]}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects a previously edited template, including its first draft.
    with output.open("x", encoding="utf-8") as stream:
        json.dump(template, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    return len(template)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path)
    parser.add_argument("--claim-template",action="store_true", help="write a new editable claim mapping with note hashes")
    parser.add_argument("--rev",default="HEAD")
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--claims",type=Path)
    parser.add_argument("--imports",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args(argv)
    def load(path):
        return json.loads(path.read_bytes()) if path is not None else {}
    if args.claim_template:
        print(json.dumps({"templates":write_template(load(args.manifest), args.out)}))
        return
    if args.repo is None:
        parser.error("--repo is required to compile records")
    print(json.dumps(compile_records(args.repo, args.rev, load(args.manifest), load(args.claims),
                                     load(args.imports), args.out), sort_keys=True))


if __name__ == "__main__":
    main()
