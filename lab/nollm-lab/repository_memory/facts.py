"""Compile a committed Git tree to deterministic, evidence-anchored structural facts (stdlib only)."""
from __future__ import annotations

import argparse
import ast
import codecs
from collections import Counter, defaultdict
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import tempfile
import warnings

from extra_languages import EXTRA_LANGUAGES, parse_extra


LANGUAGES = {
    ".py": "python", ".pyi": "python_stub", ".c": "c", ".cc": "cpp", ".cpp": "cpp",
    ".cxx": "cpp", ".h": "c_header", ".hh": "cpp_header", ".hpp": "cpp_header",
    ".hxx": "cpp_header", ".cmake": "cmake", ".rs": "rust", ".cs": "csharp",
    ".js": "javascript", ".mjs": "javascript", ".ts": "typescript", ".css": "css",
    ".html": "html", ".sql": "sql", ".sh": "shell", ".ps1": "powershell",
    ".psm1": "powershell", ".bat": "batch", ".cmd": "batch", ".md": "markdown",
    ".toml": "toml", ".yaml": "yaml", ".yml": "yaml", ".json": "json",
}
NATIVE = {"c", "cpp", "c_header", "cpp_header"}
HEADERS = {"c_header", "cpp_header"}
MODULE_SUFFIX = ".py"
IDENT = r"[A-Za-z_]\w*"


def dump(row):
    # ASCII escapes also preserve non-UTF-8 Git path bytes decoded via surrogateescape.
    return json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def inventory(repo, commit):
    files = {}
    for entry in git(repo, "ls-tree", "-rlz", "--full-tree", commit).split(b"\0"):
        if not entry:
            continue
        meta, raw_path = entry.split(b"\t", 1)
        mode, kind, oid, size = meta.decode("ascii").split()
        path = raw_path.decode("utf-8", "surrogateescape")
        name = PurePosixPath(path)
        lang = "cmake" if name.name == "CMakeLists.txt" else LANGUAGES.get(name.suffix.lower(), "other")
        files[path] = dict(path=path, parent=posixpath.dirname(path), blob=oid, bytes=int(size) if size != "-" else None,
                           kind=kind, mode=mode, lang=lang, parse="inventory_only")
    return files


def module_index(files):
    """Absolute matches use repository root and conventional src-layout root, including namespaces."""
    names = defaultdict(set)
    for p, row in files.items():
        if row["mode"] not in {"100644", "100755"} or not p.endswith(MODULE_SUFFIX):
            continue
        stem = p[:-len(MODULE_SUFFIX)]
        for candidate in {stem, stem.removeprefix("src/")}:
            pieces = candidate.split("/")
            if pieces[-1] == "__init__":
                pieces.pop()
            if pieces and all(part.isidentifier() for part in pieces):
                names[".".join(pieces)].add(p)
    return names


def relative_targets(owner, level, module, files):
    parent = posixpath.dirname(owner)
    # Anchor at the actual file: a relative import cannot cross its chosen package root.
    root = "src" if owner.startswith("src/") else ""
    if parent == root or (root and not parent.startswith(root + "/")):
        return set()
    for _ in range(level - 1):
        parent = posixpath.dirname(parent)
        if parent == root:
            return set()
    parts = [parent, *module.split(".")] if module else [parent]
    stem = posixpath.join(*parts)
    choices = [stem + ".py", stem + "/__init__.py"] if module else [stem + "/__init__.py"]
    return {p for p in choices if p in files and files[p]["mode"] in {"100644", "100755"}}


def parse_python(path, data, files, mods, symbol, edge, diagnostic):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(data, path)
    except (SyntaxError, ValueError, UnicodeError, RecursionError) as exc:
        diagnostic("py_parse_error", getattr(exc, "lineno", 0) or 0, type(exc).__name__)
        return "syntax_error"

    def add_matches(module, level, rel, line, member="", candidate=False):
        key = "." * level + module
        if member:
            module = ".".join(filter(None, (module, member)))
            key = "." * level + module
        matches = relative_targets(path, level, module, files) if level else mods.get(module, ())
        for target in sorted(matches):
            edge(target, line, rel, "candidate" if candidate or len(matches) > 1 else "exact", key)
        return bool(matches)

    def walk(node, parents=()):
        local = parents
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            local = (*parents, node.name)
            kind = {ast.ClassDef:"py_class", ast.FunctionDef:"py_function", ast.AsyncFunctionDef:"py_async_function"}[type(node)]
            symbol(node.lineno, node.end_lineno, kind, node.name, ".".join(local))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if not add_matches(alias.name, 0, "py_import", node.lineno):
                    diagnostic("py_not_in_index", node.lineno, alias.name)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            resolved = add_matches(base, node.level, "py_from_base", node.lineno)
            for alias in node.names:
                # A matching child module may be shadowed by an attribute or re-export.
                if alias.name != "*":
                    child = add_matches(base, node.level, "py_from_member", node.lineno, alias.name, True)
                    resolved = child or resolved
            if not resolved:
                diagnostic("py_not_in_index", node.lineno, "." * node.level + base)
        for child in ast.iter_child_nodes(node):
            walk(child, local)
    walk(tree)
    return "python_ast"


def c_scrub(text):
    """Remove comments and shield string/character/raw literals; preserve offsets and physical lines."""
    comment_or_literal = re.compile(
        r'/\*.*?(?:\*/|\Z)|//[^\n]*(?:\\\n[^\n]*)*|'
        r'R"([^\s()\\"]{0,16})\(.*?\)\1"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
        re.DOTALL,
    )
    def mask(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    without_comments = comment_or_literal.sub(lambda m: mask(m) if m.group().startswith(("//", "/*")) else m.group(), text)
    without_literals = comment_or_literal.sub(mask, text)
    return without_comments, without_literals


C_STMT = frozenset("""
    return co_return co_yield co_await throw new delete if else do for switch while catch try break
    continue case default goto sizeof alignof alignas __attribute__ __declspec static_assert assert using namespace typedef
""".split())
C_ATTRIBUTE = re.compile(r"(?:alignas|__attribute__|__declspec)\s*\(")


def declared_type(line):
    prefix = re.match(r"^\s*(?:typedef\s+)?(?:class|struct|enum(?:\s+(?:class|struct))?)\s+", line)
    if not prefix:
        return None
    tail = line[prefix.end():].lstrip()
    # Skip balanced attributes between class-key and name. Unclosed multiline attributes abstain.
    while tail:
        attr = C_ATTRIBUTE.match(tail)
        if attr:
            depth = 1
            stop = attr.end()
            while stop < len(tail) and depth:
                depth += (tail[stop] == "(") - (tail[stop] == ")")
                stop += 1
            if depth:
                return None
        elif tail.startswith("[["):
            stop = tail.find("]]", 2)
            if stop < 0:
                return None
            stop += 2
        else:
            name = re.match(IDENT, tail)
            if not name:
                return None
            suffix = tail[name.end():].lstrip()
            if not suffix or suffix.startswith(("{", ":", ";")) or re.match(r"final\b", suffix):
                return name.group()
            return None
        tail = tail[stop:].lstrip()
    return None


def parse_c(path, text, files, suffixes, symbol, edge, diagnostic):
    clean, code = c_scrub(text)
    plain = clean.splitlines()
    for n, line in enumerate(code.splitlines(), 1):
        include = re.match(r"^\s*#\s*include\b", line)
        if include:
            cited = re.match(r'\s*#\s*include\s*(?:"([^"\n]+)"|<([^>\n]+)>)', plain[n-1])
            if not cited:
                continue
            relative, system = cited.groups()
            token = relative or system
            direct = posixpath.normpath(posixpath.join(posixpath.dirname(path), token))
            if relative and direct in files and files[direct]["mode"] in {"100644", "100755"}:
                edge(direct, n, "c_include", "exact", token)
            else:
                # Toolchain include roots/order and preprocessor definitions are not reconstructed.
                for target in suffixes.get(token, ()):
                    edge(target, n, "c_include", "candidate", token)
                if token not in suffixes:
                    diagnostic("c_include_not_in_index", n, token)
            continue
        # Line-anchored C/C++ type declarations are lexical candidates, not ABI definitions.
        name = declared_type(line)
        if name:
            symbol(n, n, "c_type_candidate", name, name)
        if files[path]["lang"] in HEADERS:
            signature = line.replace("*", " * ").replace("&", " & ")
            fn = re.match(rf"^\s*((?:(?:{IDENT}|[&*])\s+)+)({IDENT})\s*\(", signature)
            if fn and not C_STMT.intersection(fn.group(1).split()) and fn.group(2) not in C_STMT:
                symbol(n, n, "c_function_candidate", fn.group(2), fn.group(2))
    return "c_lexical"


# Only literal arguments of resolved-target declarations produce CMake evidence.
# Bracket arguments, strings, comments and parenthesised commands are tokenized before interpretation.
CMAKE_TOKEN = re.compile(
    r'\s+|#\[(=*)\[.*?\]\1\]|\[(=*)\[.*?\]\2\]|\#[^\n]*|"(?:\\.|[^"\\])*"|[()]|(?:\\.|[^\s()"#\\])+|.', re.S,
)


def parse_cmake(path, text, files, symbol, edge, diagnostic):
    n, depth, waiting, command, argv = 1, 0, None, None, []
    for m in CMAKE_TOKEN.finditer(text):
        value = m.group()
        line = n
        n += value.count("\n")
        if value.isspace() or value.startswith("#"):
            continue
        if not depth:
            if value == "(" and waiting:
                depth, command, argv, waiting = 1, waiting.lower(), [], None
            else:
                waiting = value if re.fullmatch(IDENT, value) else None
            continue
        if value == "(":
            depth += 1
            continue
        if value == ")":
            depth -= 1
            if depth or command not in {"add_library", "add_executable", "target_sources"} or not argv:
                continue
            name = argv[0][0]
            if not re.fullmatch(r"[\w.+-]+", name):
                continue
            if command in {"add_library", "add_executable"}:
                symbol(argv[0][1], argv[0][1], "cmake_target", name, name)
                if any(value in {"IMPORTED", "ALIAS"} for value, _ in argv[1:]):
                    continue
            for arg, at in argv[1:]:
                if arg in {"STATIC", "SHARED", "MODULE", "OBJECT", "INTERFACE", "UNKNOWN", "WIN32", "MACOSX_BUNDLE", "EXCLUDE_FROM_ALL", "PRIVATE", "PUBLIC"}:
                    continue
                if "$" in arg or ";" in arg or "\\" in arg or arg.startswith("/"):
                    continue
                dst = posixpath.normpath(posixpath.join(posixpath.dirname(path), arg))
                if dst in files and files[dst]["mode"] in {"100644", "100755"}:
                    # CMake policy/imported target context can affect target_sources path resolution.
                    confidence = "candidate" if command == "target_sources" or PurePosixPath(path).name != "CMakeLists.txt" else "exact"
                    edge(dst, at, "cmake_source", confidence, name)
            continue
        if depth == 1:
            argv.append((value[1:-1] if value.startswith('"') else value, line))
    return "cmake_literal"


def source_text(data):
    for encoding, prefixes in (("utf-32", (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)),
                               ("utf-16", (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE))):
        if data.startswith(prefixes):
            return data.decode(encoding, "replace")
    return data.decode("utf-8-sig", "surrogateescape")


def compile_tree(repo, rev, destination):
    commit = git(repo, "rev-parse", "--verify", "--end-of-options", rev + "^{commit}").decode().strip()
    files = inventory(repo, commit)
    mods = module_index(files)
    suffixes = defaultdict(list)
    for path, row in files.items():
        if row["lang"] in HEADERS and row["mode"] in {"100644", "100755"}:
            parts = path.split("/")
            for i in range(len(parts)):
                suffixes["/".join(parts[i:])].append(path)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    counts = defaultdict(Counter)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temp:
        staging = Path(temp)
        with ExitStack() as stack:
            sinks = {tag:stack.enter_context((staging / (tag + ".jsonl")).open("w", encoding="utf-8", newline="\n")) for tag in ("files","symbols","edges","diagnostics")}
            cat = stack.enter_context(subprocess.Popen(["git","-C",str(repo),"cat-file","--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE))
            for path, row in files.items():
                blob = row["blob"]
                edges, symbols, diagnostics = set(), set(), set()
                def symbol(line, end, kind, name, qualname):
                    symbols.add((line, end, kind, name, qualname))
                def edge(dst, line, rel, confidence, token):
                    edges.add((line, rel, dst, confidence, token))
                def diagnostic(reason, line, token):
                    diagnostics.add((line, reason, token))
                lang = row["lang"]
                if lang in NATIVE | EXTRA_LANGUAGES | {"cmake", "python", "python_stub"} and row["mode"] in {"100644", "100755"}:
                    cat.stdin.write((blob+"\n").encode("ascii"))
                    cat.stdin.flush()
                    head = cat.stdout.readline().split()
                    if head[:2] != [blob.encode(), b"blob"]:
                        raise ValueError(f"Git did not return blob {blob}")
                    data = cat.stdout.read(int(head[2]))
                    if cat.stdout.read(1) != b"\n":
                        raise ValueError("truncated git batch response")
                    if lang in {"python","python_stub"}:
                        row["parse"] = parse_python(path, data, files, mods, symbol, edge, diagnostic)
                    else:
                        parser_text = source_text(data)
                        if lang in EXTRA_LANGUAGES:
                            row["parse"] = parse_extra(lang, path, parser_text, files, symbol, edge, diagnostic)
                        elif lang == "cmake":
                            row["parse"] = parse_cmake(path, parser_text, files, symbol, edge, diagnostic)
                        else:
                            row["parse"] = parse_c(path, parser_text, files, suffixes, symbol, edge, diagnostic)
                sinks["files"].write(dump(row)+"\n")
                counts["files"][row["parse"]] += 1
                for line,end,kind,name,qualname in sorted(symbols):
                    sinks["symbols"].write(dump(dict(path=path, blob=blob, line=line, end=end, kind=kind, name=name, qualname=qualname))+"\n")
                    counts["symbols"][kind] += 1
                for line,rel,dst,confidence,token in sorted(edges):
                    sinks["edges"].write(dump(dict(src=path, src_blob=blob, dst=dst, dst_blob=files[dst]["blob"], line=line, rel=rel,
                                                  confidence=confidence, token=token))+"\n")
                    counts["edges"][rel + "." + confidence] += 1
                for line,reason,token in sorted(diagnostics):
                    sinks["diagnostics"].write(dump(dict(path=path, blob=blob, line=line, reason=reason, token=token))+"\n")
                    counts["diagnostics"][reason] += 1
            cat.stdin.close()
            if cat.wait():
                raise RuntimeError("git cat-file failed")
        hashes = {}
        for p in sorted(staging.iterdir()):
            with p.open("rb") as stream:
                hashes[p.name] = hashlib.file_digest(stream, "sha256").hexdigest()
        manifest = {"schema":"nollm.structural-facts.v1","compiler_revision":5,"commit":commit,"counts":dict(counts),"sha256":hashes}
        (staging/"manifest.json").write_text(dump(manifest)+"\n",encoding="ascii")
        # Only publish a complete immutable directory. Repeated identical builds are safe.
        if destination.exists():
            try:
                staging.rename(destination)
            except OSError:
                if (destination/"manifest.json").is_file() and (destination/"manifest.json").read_bytes() == (staging/"manifest.json").read_bytes():
                    if all(hashlib.sha256((destination/name).read_bytes()).hexdigest() == digest for name,digest in hashes.items()):
                        return manifest
                raise FileExistsError(f"destination contains different output: {destination}")
        else:
            try:
                staging.rename(destination)
            except OSError:
                if not (destination/"manifest.json").is_file() or (destination/"manifest.json").read_bytes() != (staging/"manifest.json").read_bytes():
                    raise
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--rev", default="HEAD")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print(dump(compile_tree(a.repo, a.rev, a.out)))


if __name__ == "__main__":
    main()
