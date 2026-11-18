"""Versioned, authored observations about explicitly chosen repository sources."""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath


SCHEMA = "nollm_repo_notes_v1"


def _git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), "--literal-pathspecs", *args], capture_output=True
    )
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", "replace").strip() or "Git command failed")
    return result.stdout


def _commit(repo, rev):
    return _git(repo, "rev-parse", "--verify", "--end-of-options", f"{rev}^{{commit}}").decode().strip()


def _object_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value):
        raise ValueError("expected a full Git object ID")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _path(value):
    path = PurePosixPath(_text(value, "path"))
    if (path.is_absolute() or not path.parts or ".." in path.parts or str(path) != value
            or any(ord(c) < 32 for c in value)):
        raise ValueError(f"expected a canonical repository-relative file path: {value!r}")
    return value


def _tree(repo, commit, paths, recursive=False):
    raw = _git(repo, "ls-tree", "--full-tree", "-z", *(["-r"] if recursive else []),
               commit, "--", *paths)
    for item in raw.split(b"\0"):
        if item:
            meta, path = item.split(b"\t", 1)
            mode, kind, oid = meta.decode("ascii").split()
            yield path.decode("utf-8"), ("file" if mode in {"100644", "100755"}
                                         else kind + ":" + mode, oid)


def _files(repo, commit, paths):
    """Read only declared paths, with literal matching even for wildcard characters."""
    found = {}
    requested = sorted(set(paths))
    for start in range(0, len(requested), 100):
        found.update(_tree(repo, commit, requested[start:start + 100]))
    return found


def _rows(mapping):
    if not isinstance(mapping, dict) or not isinstance(mapping.get("notes"), list):
        raise ValueError("expected an object with a notes array")
    keys = set()
    for row in mapping["notes"]:
        if not isinstance(row, dict):
            raise ValueError("each note must be an object")
        key = _text(row.get("key"), "key")
        _text(row.get("text"), "text")
        if key in keys:
            raise ValueError(f"duplicate note key: {key}")
        keys.add(key)
    return mapping["notes"]


def _saved(manifest):
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise ValueError(f"expected manifest schema {SCHEMA}")
    rows = _rows(manifest)
    for row in rows:
        _object_id(row.get("reviewed_commit"))
        refs = row.get("evidence")
        if not isinstance(refs, list) or not refs:
            raise ValueError(f"{row['key']}: expected at least one evidence reference")
        seen = set()
        for ref in refs:
            if not isinstance(ref, dict):
                raise ValueError("each evidence reference must be an object")
            path = _path(ref.get("path"))
            _object_id(ref.get("blob"))
            if path in seen:
                raise ValueError(f"duplicate evidence reference: {path}")
            seen.add(path)
    return rows


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def manifest_path(repo, explicit):
    if explicit is not None:
        return Path(explicit)
    to_root = os.fsdecode(_git(repo, "rev-parse", "--show-cdup").rstrip(b"\n"))
    return (Path(repo) / to_root).resolve() / ".nollm" / "repository-notes.json"


def read_manifest(repo, explicit, *, optional=False):
    path = manifest_path(repo, explicit)
    try:
        return _read(path)
    except FileNotFoundError:
        if explicit is None and optional:
            return None
        raise ValueError(f"manifest not found at {path}; use brief to explore, then capture reviewed notes") from None


def _write(path, manifest):
    payload = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    if path.exists() and path.read_bytes() == payload:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        name = tmp.name
        try:
            tmp.write(payload)
            tmp.close()
            os.replace(name, path)
        finally:
            Path(name).unlink(missing_ok=True)


def capture(repo, manifest, draft_dict, rev="HEAD"):
    """Apply one reviewed batch, leaving unmentioned notes at their original evidence."""
    commit = _commit(repo, rev)
    drafts = _rows(draft_dict)
    if _object_id(draft_dict.get("reviewed_commit")) != commit:
        raise ValueError("draft reviewed_commit differs from target; review the new evidence first")
    if not drafts:
        raise ValueError("empty draft: provide at least one authored note")
    batch = []
    for row in drafts:
        also = row.get("also", [])
        if not isinstance(also, list):
            raise ValueError("also must be an array of support paths")
        paths = [_path(name) for name in [row.get("source"), *also]]
        if len(set(paths)) != len(paths):
            raise ValueError(f"{row['key']}: evidence paths must be distinct")
        batch.append((row, paths))
    files = _files(repo, commit, (p for _, paths in batch for p in paths))
    path = Path(manifest)
    by_key = {n["key"]: n for n in _saved(_read(path))} if path.exists() else {}
    for row, paths in batch:
        refs = []
        for name in paths:
            kind, oid = files.get(name, ("missing", None))
            if kind != "file":
                raise ValueError(f"{name}: expected a tracked regular file at {commit} (got {kind})")
            refs.append({"path": name, "blob": oid})
        by_key[row["key"]] = {"key": row["key"], "text": row["text"],
                              "reviewed_commit": commit, "evidence": refs}
    result = {"schema": SCHEMA, "notes": [by_key[key] for key in sorted(by_key)]}
    _write(path, result)
    return result


def _compare(repo, commit, notes):
    files = _files(repo, commit, (ref["path"] for n in notes for ref in n["evidence"]))
    result = []
    for note in notes:
        changes = []
        for ref in note["evidence"]:
            kind, oid = files.get(ref["path"], ("missing", None))
            if kind != "file" or oid != ref["blob"]:
                changes.append({"path": ref["path"], "expected": ref["blob"], "actual": oid,
                                "reason": "changed" if kind == "file" else kind})
        deleted = any(c["reason"] == "missing" for c in changes)
        status = "deleted" if deleted else ("stale" if changes else "current")
        result.append({**note, "status": status, "changes": changes})
    return result


def inspect_notes(repo, manifest_dict, rev="HEAD"):
    """Compare all declared evidence to the target commit, including supporting sources."""
    commit = _commit(repo, rev)
    return {"commit": commit, "notes": _compare(repo, commit, _saved(manifest_dict))}


def inventory(repo, scopes, manifest_dict=None, rev="HEAD"):
    """List regular files in literal scopes; report changes to any evidence for their notes."""
    commit = _commit(repo, rev)
    if isinstance(scopes, str) or not scopes:
        raise ValueError("provide one or more literal scope paths ('.' for the entire repository)")
    scopes = sorted({"." if scope == "." else _path(scope) for scope in scopes})
    all_paths = "." in scopes

    def within(path):
        return all_paths or any(path == s or path.startswith(s + "/") for s in scopes)

    notes = _saved(manifest_dict) if manifest_dict is not None else []
    primary, support, touched = {}, {}, []
    for note in notes:
        hits = [i for i, ref in enumerate(note["evidence"]) if within(ref["path"])]
        if hits:
            touched.append(note)
            for i in hits:
                index = primary if i == 0 else support
                index.setdefault(note["evidence"][i]["path"], []).append(note["key"])
    files = []
    counts = {"primary": 0, "support": 0, "unrecorded": 0}
    for path, (kind, blob) in _tree(repo, commit, [] if all_paths else scopes, recursive=True):
        if kind == "file":
            main = sorted(primary.get(path, []))
            also = sorted(support.get(path, []))
            role = "primary" if main else ("support" if also else "unrecorded")
            counts[role] += 1
            files.append({"path": path, "blob": blob, "role": role, "primary": main, "support": also})
    review = [{k: note[k] for k in ("key", "status", "changes")}
              for note in _compare(repo, commit, touched) if note["status"] != "current"]
    return {"commit": commit, "scopes": scopes, "counts": counts, "files": files, "review": review}


def format_note(note):
    """Render one reviewed note and ordered references for the host's reading view."""
    refs = ", ".join(f"{r['path']}@{r['blob'][:12]}" for r in note["evidence"])
    return f"{note['key']}: {note['text']}\n  {refs}"


def brief(repo, scopes, manifest, rev, limit):
    """Show bounded orientation from the committed tree and fresh authored notes."""
    if limit < 1:
        raise ValueError("limit must be positive")
    report = inventory(repo, scopes, manifest, rev)
    files = report["files"]
    review = report["review"]
    needs_review = {row["key"] for row in review}
    cited = {key for file in files for key in file["primary"] + file["support"]}
    rows = manifest["notes"] if manifest is not None else []
    current_keys = cited - needs_review
    current = sorted((n for n in rows if n["key"] in current_keys), key=lambda n: n["key"])
    gaps = [file["path"] for file in files if file["role"] == "unrecorded"]
    # Offer authored project entrances first when the target has no notes yet.
    entrances = {"readme", "agents", "architecture", "contributing"}
    gaps.sort(key=lambda p: (PurePosixPath(p).stem.casefold() not in entrances, p.count("/"), p))
    counts = report["counts"]
    lines = [f"Commit {report['commit']} | Scope {', '.join(report['scopes'])}",
             f"Tracked files {len(files)} | {counts['primary']} primary, {counts['support']} support, "
             f"{counts['unrecorded']} unrecorded"]

    def section(title, items, render):
        lines.append(f"\n{title} ({len(items)})")
        lines.extend(render(item) for item in items[:limit])
        if len(items) > limit:
            lines.append(f"  ... {len(items) - limit} more")

    section("Current notes", current, format_note)
    section("Needs review", review, lambda n: n["key"] + ": " + ", ".join(c["path"] for c in n["changes"]))
    section("Unrecorded paths", gaps, str)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("brief", "capture", "status", "review", "view", "inventory", "source"):
        p = commands.add_parser(name)
        p.add_argument("--repo", default=".", help="path to local Git repository")
        p.add_argument("--rev", default="HEAD", help="revision to inspect (committed tree only)")
        p.add_argument("--manifest", type=Path, help="default: .nollm/repository-notes.json at the Git root")
        if name == "capture":
            p.add_argument("--draft", required=True, type=Path)
        if name in ("brief", "inventory"):
            p.add_argument("--scope", action="append", required=name == "inventory",
                           help="literal repo-relative file or directory; '.' for all")
        if name == "brief":
            p.add_argument("--limit", type=int, default=5, help="maximum entries per section (default: 5)")
        if name == "source":
            p.add_argument("--key", required=True, help="key of an already selected note")
            p.add_argument("--evidence-index", type=int, default=0, help="0 for the primary source; 1 and up for support")
    args = parser.parse_args(argv)
    try:
        if args.command == "brief":
            manifest = read_manifest(args.repo, args.manifest, optional=True)
            print(brief(args.repo, args.scope or ["."], manifest, args.rev, args.limit))
        elif args.command == "inventory":
            manifest = read_manifest(args.repo, args.manifest, optional=True)
            print(json.dumps(inventory(args.repo, args.scope, manifest, args.rev), ensure_ascii=False, indent=2))
        elif args.command == "capture":
            draft = _read(args.draft)
            result = capture(args.repo, manifest_path(args.repo, args.manifest), draft, args.rev)
            print(f"Captured {len(draft['notes'])} reviewed notes; {len(result['notes'])} in manifest.")
        elif args.command == "source":
            rows = _saved(read_manifest(args.repo, args.manifest))
            note = next((n for n in rows if n["key"] == args.key), None)
            if note is None:
                raise ValueError(f"unknown note: {args.key}")
            commit = _commit(args.repo, args.rev)
            checked = _compare(args.repo, commit, [note])[0]
            if checked["status"] != "current":
                raise ValueError(f"{args.key}: {checked['status']} at {commit}; reviewed at {note['reviewed_commit']}")
            if not 0 <= args.evidence_index < len(note["evidence"]):
                raise ValueError("evidence index is outside this note's sources")
            blob = note["evidence"][args.evidence_index]["blob"]
            sys.stdout.buffer.write(_git(args.repo, "cat-file", "blob", blob))
        else:
            result = inspect_notes(args.repo, read_manifest(args.repo, args.manifest), args.rev)
            if args.command in ("status", "review"):
                if args.command == "review":
                    result["notes"] = [n for n in result["notes"] if n["status"] != "current"]
                for note in result["notes"]:
                    if note["status"] != "current":
                        del note["text"]
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for note in result["notes"]:
                    if note["status"] == "current":
                        print(format_note(note))
    except (OSError, ValueError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
