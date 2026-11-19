"""Import the semantic fields of repository-root AOCI code volumes, or render them canonically."""
import argparse
import json
import re
from pathlib import Path

SLOTS = ("F", "R", "A", "S")
AXES = ("A", "B", "C", "D", "E")
HEADER = "#AOCI-CODE-VOLUME: 1"


def _parts(tag):
    if not tag or "," in tag or "，" in tag:
        raise ValueError(f"unsupported tag {tag!r}")
    if "." in tag:
        values = tag.split(".")
        if len(values) not in (4, 5) or any(not v or v != v.strip() for v in values):
            raise ValueError(f"bad dotted tag {tag!r}")
        axis = AXES if len(values) == 5 else ("A", "B", "C", "E")
        return dict(zip(axis, values))
    first = re.search("[0-9]", tag)
    if not first or first.start() < 2 or first.end() >= len(tag):
        raise ValueError(f"bad compact tag {tag!r}")
    i = first.start()
    result = {"A": tag[0], "B": tag[1:i], "C": tag[i], "E": tag[-1]}
    if tag[i+1:-1]:
        result["D"] = tag[i+1:-1]
    return result


def _path_parts(path):
    parts = path.split("/")
    if any(v in {"", ".", ".."} for v in parts) or "\\" in path or "\x00" in path:
        raise ValueError(f"invalid repository-relative path {path!r}")
    return parts


def parse_volume(text):
    """Return unique code objects, in source order. Reject unsupported/lossy syntax."""
    lines = text.removeprefix("\ufeff").splitlines()
    if not lines or lines[0] != HEADER:
        raise ValueError("expected a repository-root AOCI v1 code volume")
    rows = []
    seen = set()
    prefix = None
    for line_no, line in enumerate(lines[1:], 2):
        if not line.strip():
            continue
        header = re.fullmatch(r"===/<repository>/(.*?)===", line)
        if header:
            prefix = header.group(1).rstrip("/")
            if prefix:
                _path_parts(prefix)
            continue
        entry = re.fullmatch(r"(\S.*?)\[([^\[\]]+)\]:\s?(.*)", line)
        if not entry:
            if line.startswith("#"):
                continue
            raise ValueError(f"bad entry on line {line_no}")
        if prefix is None or line.startswith("==="):
            raise ValueError(f"unsupported volume layout on line {line_no}")
        filename, tag, body = entry.groups()
        _path_parts(filename)
        ident = "code:" + (prefix + "/" if prefix else "") + filename
        if ident in seen:
            raise ValueError(f"duplicate identity {ident} on line {line_no}")
        seen.add(ident)
        fields = {}
        for seg in body.split(" | "):
            head, sep, value = seg.strip().partition(":")
            if not sep or head not in SLOTS or head in fields:
                raise ValueError(f"unsupported or repeated slot on line {line_no}")
            fields[head] = value.strip()
        rows.append({"id": ident, "tags": _parts(tag), "fields": fields})
    return rows


def parse_dictionary(text, kind="code"):
    """Read the English canonical dictionary headings and code-label pairs of AOCI META v1."""
    if kind != "code":
        raise ValueError("this adapter supports code volumes")
    sections = re.split(r"^#\[Tag dictionary: ([^\]]+)\]\s*$", text, flags=re.M)
    if kind not in sections[1::2]:
        raise ValueError(f"dictionary {kind!r} not found")
    body = sections[sections.index(kind, 1)+1]
    out = {v: [] for v in AXES}
    names = {"A": "Layer", "B": "Module", "C": "Importance", "D": "Trait", "E": "Scale"}
    seen = set()
    for line in body.splitlines():
        match = re.fullmatch(r"#([ABCDE])\s+([^:]+):\s*(.*)", line)
        if not match:
            continue
        axis, name, values = match.groups()
        if name != names[axis] or axis in seen:
            raise ValueError(f"unsupported or duplicate dictionary declaration for {axis}")
        seen.add(axis)
        pattern = {"A": r"[A-Za-z]", "C": r"[1-9]", "E": r"[A-Za-z]"}.get(axis,r"[A-Za-z]+")
        for token in values.split():
            symbol, sep, label = token.partition("-")
            if not sep or not label or not re.fullmatch(pattern,symbol) or symbol in out[axis]:
                raise ValueError(f"unsupported dictionary token for {axis}: {token}")
            out[axis].append(symbol)
    if any(not out[a] for a in ("A", "B", "C", "E")):
        raise ValueError("incomplete code dictionary")
    return out


def _render_tag(tags):
    required = {"A", "B", "C", "E"}
    if not required <= set(tags) <= set(AXES):
        raise ValueError("invalid tag dimensions")
    terms = [tags[a] for a in AXES if a in tags]
    if not all(isinstance(t, str) and t and t == t.strip() and not any(c in t for c in ".,，[]\r\n") for t in terms):
        raise ValueError("unsupported tag dimension value")
    compact = "".join(terms)
    try:
        if _parts(compact) == tags:
            return compact
    except ValueError:
        pass
    return ".".join(terms)


def render_volume(rows):
    """Emit the normalized equivalence class. Comments, layout trivia and raw spellings are not reconstructed."""
    lines = [HEADER]
    last_dir = None
    seen = set()
    for row in rows:
        ident = row["id"]
        if not isinstance(ident,str) or not ident.startswith("code:") or ident in seen:
            raise ValueError(f"unsupported or duplicate identity {ident!r}")
        seen.add(ident)
        parts = _path_parts(ident[5:])
        dirname = "/".join(parts[:-1])
        if dirname != last_dir:
            lines.extend(["", "===/<repository>/" + (dirname+"/" if dirname else "") + "==="])
            last_dir = dirname
        fields = row["fields"]
        if not fields or not set(fields) <= set(SLOTS):
            raise ValueError("unsupported or missing field set")
        for val in fields.values():
            if not isinstance(val, str) or val != val.strip() or "\r" in val or "\n" in val or " | " in val:
                raise ValueError("unrepresentable slot value")
        body = " | ".join(k+":"+fields[k] for k in SLOTS if k in fields)
        lines.append(f"{parts[-1]}[{_render_tag(row['tags'])}]: {body}")
    return "\n".join(lines)+"\n"


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--volume",type=Path,required=True)
    p.add_argument("--meta",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--dictionary-out",type=Path,required=True)
    a=p.parse_args()
    if len({a.volume.resolve(),a.meta.resolve(),a.out.resolve(),a.dictionary_out.resolve()})!=4:
        p.error("input and output paths must be distinct")
    try:
        dictionary=parse_dictionary(a.meta.read_text(encoding="utf-8"))
        rows=parse_volume(a.volume.read_text(encoding="utf-8"))
        for row in rows:
            if any(value not in dictionary[axis] for axis,value in row["tags"].items()):
                raise ValueError("undeclared dictionary value for "+row["id"])
        if parse_volume(render_volume(rows)) != rows:
            raise ValueError("round-trip check failed")
        for path, value in [(a.out,rows),(a.dictionary_out,dictionary)]:
            path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    except (ValueError,OSError) as err:
        p.exit(2, f"{p.prog}: {err}\n")


if __name__=="__main__":
    main()
