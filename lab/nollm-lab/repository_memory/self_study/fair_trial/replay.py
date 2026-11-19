"""Seal observed calls, then regenerate their exact visible bytes in fresh sessions."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED


HERE = Path(__file__).resolve().parent
GATEWAY = HERE / "gateway.py"
SCHEMA = "nollm-fair-observations-v1"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def summarize_event(event):
    return {
        "argv": [event["action"], *event["args"]],
        "visible_sha256": sha256(event["text"].encode("utf-8")).hexdigest(),
        "tokens": event["tokens"],
        "bucket": event["bucket"],
        "truncated": event["truncated"],
        "changes": event["changes"],
    }


def events_at(session):
    return [json.loads(line) for line in (session / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def field_identity(field):
    return {p: digest(field / p) for p in ("layout.json", "core/current_state.json")}


def collect(sessions, out, raw_zip):
    questions = {}
    cases = []
    arms = Counter()
    fields = set()
    for conf in sorted(sessions.glob("*/config.json")):
        session = conf.parent
        config = read_json(conf)
        question = config["id"]
        if questions.setdefault(question, config["question"]) != config["question"]:
            raise ValueError(f"question text differs between sessions for {question}")
        arms[question, config["arm"]] += 1
        fields.add(Path(config["field"]).resolve())
        native = session / "native.json"
        cases.append({
            "session": session.name, "question": question, "arm": config["arm"],
            "calls": [summarize_event(e) for e in events_at(session)],
            "native_sha256": digest(native) if native.exists() else None,
            "submission": read_json(session / "answer.json"),
        })
    expected = Counter((q, arm) for q in questions for arm in ("search", "flat", "surface"))
    if len(questions) != 6 or arms != expected or len(fields) != 1:
        raise ValueError("expected six questions with one participant in each arm on the same field")
    field = fields.pop()
    fixture = {
        "schema": SCHEMA, "source_revision": read_json(field / "layout.json")["revision"],
        "gateway_sha256": digest(GATEWAY), "field_sha256": field_identity(field),
        "questions": questions, "sessions": cases,
    }
    write_json(out, fixture)
    if raw_zip:
        with ZipFile(raw_zip, "w", compression=ZIP_DEFLATED, compresslevel=8) as archive:
            archive.write(out, "observations.json")
            for case in cases:
                session = sessions / case["session"]
                for name in ("events.jsonl", "native.json", "answer.json"):
                    if (session / name).is_file():
                        archive.write(session / name, f"sessions/{session.name}/{name}")
            archive.writestr("README.txt", "Raw model-visible gateway texts are in sessions/*/events.jsonl. "
                             "Observations contain the exact calls, meter counts, submitted answers, and digests. "
                             "Use the experiment branch's fair_trial/replay.py verify on its pinned fitted field.\n")
    return {"sessions": len(cases), "calls": sum(len(c["calls"]) for c in cases),
            "native_recalls": sum(c["native_sha256"] is not None for c in cases)}


def verify(fixture_path, repo, field, destination):
    import tiktoken

    encoder = tiktoken.get_encoding("o200k_base")
    fixture = read_json(fixture_path)
    if fixture["schema"] != SCHEMA or digest(GATEWAY) != fixture["gateway_sha256"]:
        raise ValueError("fixture schema or gateway version differs")
    if field_identity(field) != fixture["field_sha256"]:
        raise ValueError("the fitted field layout or Core state differs from the recorded input")
    subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f'{fixture["source_revision"]}^{{commit}}'], check=True)
    totals = Counter()
    for case in fixture["sessions"]:
        session = destination / case["session"]
        session.mkdir()
        config = {"id": case["question"], "question": fixture["questions"][case["question"]],
                  "arm": case["arm"], "repo": str(repo.resolve()), "field": str(field.resolve())}
        write_json(session / "config.json", config)
        for i, call in enumerate(case["calls"], 1):
            cmd = [sys.executable, str(GATEWAY), "--session", str(session), *call["argv"]]
            seen = subprocess.run(cmd, check=True, stdout=subprocess.PIPE).stdout
            if sha256(seen).hexdigest() != call["visible_sha256"]:
                raise ValueError(f"{session.name} call {i} displayed different bytes")
            count = len(encoder.encode_ordinary(seen.decode("utf-8")))
            if count != call["tokens"]:
                raise ValueError(f"{session.name} call {i} visible token count differs")
            totals[call["bucket"] + "_tokens"] += count
        replayed = [summarize_event(e) for e in events_at(session)]
        if replayed != case["calls"]:
            raise ValueError(f"{session.name} meter, truncation, or state transitions differ")
        native = session / "native.json"
        if (digest(native) if native.exists() else None) != case["native_sha256"]:
            raise ValueError(f"{session.name} native readback differs")
        write_json(session / "answer.json", case["submission"])
        totals.update(sessions=1, calls=len(replayed), native_recalls=int(native.exists()))
    return totals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    seal = commands.add_parser("collect")
    seal.add_argument("--sessions", type=Path, required=True)
    seal.add_argument("--out", type=Path, required=True)
    seal.add_argument("--raw-zip", type=Path)
    replay = commands.add_parser("verify")
    replay.add_argument("--fixture", type=Path, required=True)
    replay.add_argument("--repo", type=Path, required=True)
    replay.add_argument("--field", type=Path, required=True)
    replay.add_argument("--emit-traces", type=Path, help="new output directory for replayed ledgers and submissions")
    args = parser.parse_args()
    if args.action == "collect":
        result = collect(args.sessions, args.out, args.raw_zip)
    elif args.emit_traces:
        args.emit_traces.mkdir(parents=True)
        result = verify(args.fixture, args.repo, args.field, args.emit_traces)
    else:
        with TemporaryDirectory() as temp:
            result = verify(args.fixture, args.repo, args.field, Path(temp))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
