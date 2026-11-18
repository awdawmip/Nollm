"""Participant interface. Run inside the trial directory created by compare.py."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("start")
    search = commands.add_parser("search", help="search source and tests, up to 60 matching lines")
    search.add_argument("pattern", help="ripgrep regular expression")
    read = commands.add_parser("read")
    read.add_argument("path")
    read.add_argument("first", nargs="?", type=int, default=1)
    read.add_argument("last", nargs="?", type=int)
    args = parser.parse_args()
    trial = Path(__file__).resolve().parent
    tree = trial / "tree"
    if args.command == "start":
        body = (trial / "packet.txt").read_text(encoding="utf-8")
    elif args.command == "search":
        result = subprocess.run(["rg", "--no-heading", "--color=never", "--sort", "path",
                                 "-n", "-e", args.pattern, "packages",
                                 *(["docs"] if (tree / "docs").is_dir() else [])],
                                cwd=tree, capture_output=True, text=True)
        if result.returncode not in (0, 1):
            parser.error(result.stderr)
        body = "".join(result.stdout.splitlines(keepends=True)[:60]) or "(no matches)\n"
    else:
        path = (tree / args.path).resolve()
        if not any(path.is_relative_to(tree / root) for root in ("packages", "docs")) or not path.is_file():
            parser.error("supply a source path relative to tree/")
        if args.first < 1 or (args.last is not None and args.last < args.first):
            parser.error("invalid line range")
        body = "".join(path.read_text(encoding="utf-8").splitlines(keepends=True)[args.first - 1:args.last])
    event = {"args": vars(args), "text": body}
    with (trial / "trace.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    sys.stdout.buffer.write(body.encode("utf-8"))


if __name__ == "__main__":
    main()
