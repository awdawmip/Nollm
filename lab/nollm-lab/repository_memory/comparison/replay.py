"""Regrade an archived matrix on fresh package snapshots and verify recorded inputs."""
import argparse
from hashlib import sha256
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory

from compare import HERE, prepare
from score import score


def replay(repo, snapshot, receipt, temp):
    spec = json.loads((receipt / "trial.json").read_text())
    trial = temp / receipt.name
    if repo is not None:
        prepare(repo, trial, spec["task"], spec["arm"])
        if (trial / "packet.txt").read_bytes() != (receipt / "packet.txt").read_bytes():
            raise ValueError(f"{receipt.name}: generated starting packet differs")
    else:
        tree = trial / "tree"
        tree.mkdir(parents=True)
        with tarfile.open(snapshot) as archive:
            archive.extractall(tree, filter="data")
        if spec["task"] != "digest":
            shutil.rmtree(tree / "docs")
        shutil.copyfile(HERE / "observe.py", trial / "observe.py")
        for key in ("trial.json", "packet.txt"):
            shutil.copyfile(receipt / key, trial / key)
    expected = json.loads((receipt / "score.json").read_text())
    patch = receipt / "candidate.patch"
    if sha256(patch.read_bytes()).hexdigest() != expected.pop("patch_sha256"):
        raise ValueError(f"{receipt.name}: patch hash differs")
    applied = False
    events = [json.loads(line) for line in (receipt / "trace.jsonl").read_text().splitlines()]
    for index, event in enumerate(events, 1):
        args = event["args"]
        command = [sys.executable, str(trial / "observe.py"), args["command"]]
        if args["command"] == "search":
            command.append(args["pattern"])
        elif args["command"] == "read":
            command.extend([args["path"], str(args["first"])])
            if args["last"] is not None:
                command.append(str(args["last"]))
        body = subprocess.check_output(command)
        if body != event["text"].encode() and not applied:
            # Participants sometimes inspect their own edits. Check that response on the
            # patched tree, removing the speculative read from the observation log.
            trace = trial / "trace.jsonl"
            trace.write_bytes(b"".join(trace.read_bytes().splitlines(keepends=True)[:-1]))
            subprocess.run(["git", "-C", trial / "tree", "apply", patch], check=True)
            applied = True
            body = subprocess.check_output(command)
        if body != event["text"].encode():
            raise ValueError(f"{receipt.name}: response {index} differs from the tree")
    if not applied:
        subprocess.run(["git", "-C", trial / "tree", "apply", patch], check=True)
    shutil.copyfile(receipt / "evidence.json", trial / "evidence.json")
    if (receipt / "usage.json").exists():
        shutil.copyfile(receipt / "usage.json", trial / "usage.json")
    actual = score(trial)
    if actual != expected:
        raise ValueError(f"{receipt.name}: scores differ")
    print(f"{receipt.name}: replayed {actual['observed_tokens']} observed tokens, success={actual['success']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--repo", type=Path, help="regenerate arm packets from the Nollm checkout")
    source.add_argument("--snapshot", type=Path, help="replay archived packets on the bundled Git snapshot")
    parser.add_argument("--receipts", required=True, type=Path)
    args = parser.parse_args()
    receipts = sorted(p.parent for p in args.receipts.glob("*/score.json"))
    if not receipts:
        parser.error("no archived trials found")
    with TemporaryDirectory() as temp:
        for receipt in receipts:
            replay(args.repo.resolve() if args.repo else None, args.snapshot, receipt.resolve(), Path(temp))


if __name__ == "__main__":
    main()
