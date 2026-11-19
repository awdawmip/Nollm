"""Meter discovery and pinned-source reads for one independent benchmark participant."""
import argparse
import ast
import fcntl
import json
from pathlib import Path
import re
import subprocess
import sys

import tiktoken

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
# vertical_atlas makes the same source-checkout Core and Access available.
from vertical_atlas import SOURCE_REVISION
import coverage_cli
from nollm_core import PhysicalFieldScope, RecallBudget

LIMIT = {"discovery": 6000, "source": 5000}
MAX_FILES = 3
SURFACE_CALLS = 12
NEIGHBOR_BUDGET = RecallBudget(2, 64, 2, 0, 0, 10)
SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)
START = """Use only the assigned discovery channel. The discovery budget is 6000 visible tokens.
search REGEX [PAGE] gives source locations. flat [PAGE] gives eleven AOCI notes per page.
surface shows the first candidate page; surface ID opens one shown candidate, surface next pages, surface back reopens the previous page. Choose exactly one physical entry and run recall once.
open PATH [FIRST [LAST]] shows numbered source; default 100 lines. find PATH REGEX lists matching line numbers inside the file. Either opens the file. You may inspect three distinct files within 5000 visible source tokens. Pages and line numbers start at 1. status reports usage. Cite only evidence you inspected.
"""


def fit_text(text, remaining, encoder):
    tokens = encoder.encode_ordinary(text)
    if len(tokens) <= remaining:
        return text, len(tokens), False
    marker = "\n[visible token limit reached]\n"
    if len(encoder.encode_ordinary(marker)) > remaining:
        marker = ""
    prefix_length = remaining - len(encoder.encode_ordinary(marker))
    while prefix_length >= 0:
        prefix = encoder.decode_bytes(tokens[:prefix_length]).decode("utf-8", errors="ignore")
        visible = prefix + marker
        count = len(encoder.encode_ordinary(visible))
        if count <= remaining:
            return visible, count, True
        prefix_length -= 1
    return "", 0, True


def state_after(events):
    state = {"spent": {"discovery": 0, "source": 0}, "opened": [], "pages": [],
             "surface_calls": 0, "entry": None, "recalled": False, "started": False}
    for event in events:
        if event["bucket"] in LIMIT:
            state["spent"][event["bucket"]] += event["tokens"]
        state.update(event["changes"])
    return state


def pinned_lines(repo, path):
    data = subprocess.check_output(["git", "-C", str(repo), "show", f"{SOURCE_REVISION}:{path}"])
    return data.decode("utf-8").splitlines()


def paginate(rows, args, page_size):
    page = int(args[0]) if args else 1
    last = max(1, (len(rows) + page_size - 1) // page_size)
    if len(args) > 1 or not 1 <= page <= last:
        raise ValueError(f"page must be from 1 to {last}")
    return f"Page {page}/{last}\n" + "\n".join(rows[(page - 1) * page_size:page * page_size])


def source_search(repo, paths, args):
    if not args:
        raise ValueError("search REGEX [PAGE]")
    pattern = re.compile(args[0], re.I)
    results = []
    for path in paths:
        lines = pinned_lines(repo, path)
        hits = [n for n, line in enumerate(lines, 1) if pattern.search(line)]
        name_hit = bool(pattern.search(path))
        if not name_hit and not hits:
            continue
        tree = ast.parse("\n".join(lines), filename=path)
        definitions = [node for node in ast.walk(tree)
                       if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
        contexts = []
        for n in hits[:8]:
            local = max((node for node in definitions if node.lineno <= n <= node.end_lineno),
                        key=lambda node: node.lineno, default=None)
            contexts.append(str(n) + (f"({local.name})" if local else ""))
        row = f"{path} | {len(hits)} matching lines | " + ", ".join(contexts)
        results.append((not name_hit, -len(hits), path, row))
    return paginate([item[-1] for item in sorted(results)], args[1:], 12)


def format_page(page):
    if page["kind"] == "entry":
        return f"Selected physical entry {page['entry']}. Run recall."
    header = f"{page['kind']} order={page['order']} more={page['has_more']}"
    rows = [header]
    for cell in page["candidates"]:
        location = cell.get("window", cell.get("physical_cell"))
        rows.append(f"{cell['id']} {location} ({cell['native_atoms']} atoms)")
        rows.extend("  " + text for text in cell["previews"])
    return "\n".join(rows)


def surface_action(field, state, args):
    if state["entry"] is not None or state["surface_calls"] >= SURFACE_CALLS:
        raise ValueError("entry already selected or surface call cap reached")
    if len(args) > 1 or (state["surface_calls"] == 0 and args):
        raise ValueError("start with surface; then give one shown ID, next, or back")
    choices = list(state["pages"])
    if args == ["back"]:
        if not choices:
            raise ValueError("already at first page")
        choices.pop()
    elif args:
        choices.append(args[0])
    page = coverage_cli.surface(field, SCOPE, 1, choices, 4, SURFACE_CALLS)
    updates = {"pages": choices, "surface_calls": state["surface_calls"] + 1}
    if page["kind"] == "entry":
        updates["entry"] = page["entry"]
    return format_page(page), updates


def retrieve(session, config, manifest, state, action, args):
    files = manifest["files"]
    repo, field = Path(config["repo"]), Path(config["field"])
    if action == "start" and not args and not state["started"]:
        return config["question"] + "\n\n" + START, {"started": True}
    if not state["started"]:
        raise ValueError("run start first")
    if action == "status" and not args:
        return json.dumps({k: state[k] for k in ("spent", "opened", "surface_calls", "entry", "recalled")}), {}
    if action in ("open", "find"):
        if not args or args[0] not in files:
            raise ValueError("supply a repository-relative source path in the corpus")
        path = args[0]
        if config["arm"] == "surface":
            if not state["recalled"]:
                raise ValueError("select one physical entry and recall first")
            raw = json.loads((session / "native.json").read_text())
            allowed = {item["source"].split(":", 1)[1] for item in raw["items"] if item["status"] == "current"}
            if path not in allowed:
                raise ValueError("path was not returned by the physical recall")
        opened = list(state["opened"])
        if path not in opened:
            if len(opened) >= MAX_FILES:
                raise ValueError("three distinct source files already opened")
            opened.append(path)
        lines = pinned_lines(repo, path)
        if action == "find":
            if len(args) != 2:
                raise ValueError("find PATH REGEX")
            pattern = re.compile(args[1], re.I)
            hits = [str(n) for n, line in enumerate(lines, 1) if pattern.search(line)]
            return path + " | matching lines: " + (", ".join(hits) or "none"), {"opened": opened}
        first = int(args[1]) if len(args) >= 2 else 1
        last = int(args[2]) if len(args) >= 3 else first + 99
        if len(args) > 3 or first < 1 or last < first:
            raise ValueError("open PATH [FIRST [LAST]], numbered from 1")
        head = f"{path} ({len(lines)} lines)"
        visible = [f"{n:4} {lines[n-1]}" for n in range(first, min(last, len(lines))+1)]
        return "\n".join([head, *visible]), {"opened": opened}
    if config["arm"] == "search" and action == "search":
        return source_search(repo, sorted(files), args), {}
    if config["arm"] == "flat" and action == "flat":
        return paginate([files[p]["text"] for p in sorted(files)], args, 11), {}
    if config["arm"] == "surface" and action == "surface":
        return surface_action(field, state, args)
    if config["arm"] == "surface" and action == "recall" and not args:
        if not state["entry"] or state["recalled"]:
            raise ValueError("select a physical entry; only one recall is available")
        raw = coverage_cli.recall(repo, SOURCE_REVISION, field, coverage_cli.address(*state["entry"]),
                                  "both", NEIGHBOR_BUDGET)
        (session / "native.json").write_text(json.dumps(raw, ensure_ascii=False) + "\n")
        rows = [f"Native results from {state['entry']} ({len(raw['items'])} handles)"]
        for row in raw["items"]:
            path = row["source"].split(":", 1)[1]
            rows.append(f"{path} | score={row['score_q16']} | {'/'.join(row['path']) or 'entry'}")
        rows.extend(row["text"] for row in raw["items"] if row["status"] == "current")
        return "\n".join(rows), {"recalled": True}
    raise ValueError("action unavailable for this session")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("action")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    encoder = tiktoken.get_encoding("o200k_base")
    config = json.loads((args.session / "config.json").read_text())
    manifest = json.loads((Path(config["field"]) / "layout.json").read_text())
    if manifest["revision"] != SOURCE_REVISION or len(manifest["files"]) != 44:
        raise ValueError("session field does not match the pinned 44-file source corpus")
    with (args.session / "events.jsonl").open("a+") as ledger:
        fcntl.flock(ledger, fcntl.LOCK_EX)
        ledger.seek(0)
        state = state_after([json.loads(line) for line in ledger])
        bucket = "source" if args.action in ("open", "find") else "discovery"
        updates = {}
        if args.action == "start" and not args.args and not state["started"]:
            bucket = "control"
        remaining = LIMIT[bucket] - state["spent"][bucket] if bucket in LIMIT else sys.maxsize
        if remaining == 0:
            text = ""
        else:
            try:
                text, updates = retrieve(args.session, config, manifest, state, args.action, args.args)
            except (ValueError, re.error, RuntimeError, IndexError, KeyError) as exc:
                text = f"Action failed: {exc}"
            text = text.rstrip("\n") + "\n"
        visible, count, truncated = fit_text(text, remaining, encoder)
        event = {"action": args.action, "args": args.args, "bucket": bucket, "tokens": count,
                 "text": visible, "truncated": truncated, "changes": updates}
        ledger.write(json.dumps(event, ensure_ascii=False) + "\n")
        ledger.flush()
        sys.stdout.write(visible)


if __name__ == "__main__":
    main()
