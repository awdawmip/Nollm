"""Score blinded semantic judgments and independently ground citations in visible source."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

import tiktoken


FREEZE = Path(__file__).with_name("freeze.json")
LINE = re.compile(r"^ *(\d+) ")
CLIP = "\n[visible token limit reached]\n"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_lines(events):
    visible = defaultdict(set)
    opened = set()
    for event in events:
        if "opened" not in event["changes"]:
            continue
        opened.update(event["changes"]["opened"])
        if event["action"] != "open":
            continue
        path = event["args"][0]
        text = event["text"]
        if event["truncated"]:
            # The marker inserts its own newline, even in the middle of a source line.
            text = text.removesuffix(CLIP)
        for line in text.splitlines(keepends=True)[1:]:
            match = LINE.match(line)
            if match and (not event["truncated"] or line.endswith("\n")):
                visible[path].add(int(match.group(1)))
    return opened, visible


def ratio(num, den):
    return num / den if den else None


def ratios(count):
    return {
        "opened_path_precision": ratio(count["relevant_opens"], count["opened"]),
        "cited_path_precision": ratio(count["relevant_citations"], count["cited"]),
        "grounded_precision": ratio(count["grounded_files"], count["cited"]),
        "grounded_recall": ratio(count["matched_roles"], count["required_roles"]),
        "physical_precision": ratio(count.get("physical_relevant", 0), count.get("physical_returns", 0)),
    }


def evaluate(directory, question, judgment, freeze, encoder):
    config = load(directory / "config.json")
    submission = load(directory / "answer.json")
    events = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
    opened, visible = read_lines(events)
    citations = defaultdict(list)
    for citation in submission["citations"]:
        citations[citation["path"]].extend(citation["lines"])
    plausible = set()
    grounded_files = set()
    matched = {}
    for role in question["required_sources"]:
        # The current key contains no alternatives. An alternative can supply its own anchors.
        alternatives = [role, *role["alternative_paths"]]
        witness = {}
        for source in alternatives:
            path = source["path"]
            plausible.add(path)
            overlap = sorted(num for num in visible[path]
                             if any(a <= num <= b for a, b in citations.get(path, ()))
                             and any(a["start"] <= num <= a["end"] for a in source["line_anchors"]))
            if overlap:
                witness[path] = overlap
                grounded_files.add(path)
        if witness:
            matched[role["path"]] = witness

    roles = {r["path"] for r in question["required_sources"]}
    expected_atoms = {a["id"] for a in question["mandatory_atoms"]}
    atoms = judgment["atoms"]
    contradiction = judgment["material_contradiction"]
    if set(atoms) != expected_atoms or not all(type(a) is bool for a in [*atoms.values(), contradiction]):
        raise ValueError(f"invalid semantic grades for {directory.name}")
    tokens = Counter()
    for event in events:
        tokens[event["bucket"]] += event["tokens"]
    answer_text = json.dumps(submission, ensure_ascii=False, separators=(",", ":"))
    budget = freeze["visible_budget"]
    answer_tokens = len(encoder.encode_ordinary(answer_text))
    cited = set(citations)
    extra_opens, extra_cites = opened - plausible, cited - plausible
    counts = {
        "sessions": 1, "required_roles": len(roles), "matched_roles": len(matched),
        "missed_roles": len(roles) - len(matched), "opened": len(opened), "cited": len(cited),
        "relevant_opens": len(opened & plausible), "extra_opens": len(extra_opens),
        "relevant_citations": len(cited & plausible), "extra_citations": len(extra_cites),
        "grounded_files": len(grounded_files), "ungrounded_citations": len(cited - grounded_files),
        "atom_hits": sum(atoms.values()), "atom_total": len(atoms),
        "material_contradictions": int(contradiction), "gateway_calls": len(events),
        "control_tokens": tokens["control"], "discovery_tokens": tokens["discovery"],
        "source_tokens": tokens["source"], "answer_tokens": answer_tokens,
        "returned_tokens": sum(tokens.values()), "visible_including_answer": sum(tokens.values()) + answer_tokens,
    }
    limits = {
        "discovery": tokens["discovery"] <= budget["discovery_tokens"],
        "source": tokens["source"] <= budget["source_tokens"],
        "answer": answer_tokens <= budget["answer_tokens"],
        "files": max(len(cited), len(opened)) <= budget["unique_open_files"],
    }
    native_paths = []
    if config["arm"] == "surface":
        selected = [event["changes"]["entry"] for event in events if "entry" in event["changes"]]
        recalls = sum(event["changes"].get("recalled", False) for event in events)
        calls = sum("surface_calls" in event["changes"] for event in events)
        counts.update(physical_recalls=recalls, physical_entries=len(selected), surface_calls=calls)
        limits["single_entry"] = len(selected) == recalls == 1
        limits["surface_requests"] = calls <= freeze["geometry"]["max_surface_requests"]
        if recalls:
            raw = load(directory / "native.json")
            native_paths = [item["source"].split(":", 1)[1] for item in raw["items"]]
            limits["physical_source_opens"] = opened <= set(native_paths)
        counts.update(physical_returns=len(native_paths),
                      physical_relevant=sum(p in plausible for p in native_paths),
                      physical_extra=sum(p not in plausible for p in native_paths))
    if all(limits.values()) and all(atoms.values()) and len(matched) == len(roles) and not contradiction:
        outcome = "full"
    elif any(atoms.values()) or matched:
        outcome = "partial"
    else:
        outcome = "none"
    counts[outcome] = 1
    return {
        "session": directory.name, "question": config["id"], "arm": config["arm"], "outcome": outcome,
        "counts": counts, "ratios": ratios(counts), "limits": limits, "provider_usage": None,
        "witness_lines": matched, "missed_roles": sorted(roles - matched.keys()),
        "extra_open_files": sorted(extra_opens), "extra_cited_files": sorted(extra_cites),
        "ungrounded_citations": sorted(cited - grounded_files),
        "unrelated_physical_returns": [p for p in native_paths if p not in plausible],
        "atoms": atoms, "material_contradiction": contradiction,
    }


def score(sessions, gold, judgments):
    freeze = load(FREEZE)
    if hashlib.sha256(gold.read_bytes()).hexdigest() != freeze["key_sha256"]:
        raise ValueError("gold differs from the prospectively sealed key")
    questions = {q["id"]: q for q in load(gold)["questions"]}
    expected = {(q, arm) for q in questions for arm in freeze["arms"]}
    votes = load(judgments)
    encoder = tiktoken.get_encoding(freeze["visible_budget"]["encoding"])
    rows = []
    totals = defaultdict(Counter)
    for directory in sorted(sessions.glob("*/config.json")):
        directory = directory.parent
        config = load(directory / "config.json")
        pair = (config["id"], config["arm"])
        if pair not in expected or config["question"] != questions[pair[0]]["question"]:
            raise ValueError(f"unexpected or duplicate paired assignment: {directory.name}")
        expected.remove(pair)
        row = evaluate(directory, questions[pair[0]], votes[directory.name], freeze, encoder)
        totals[pair[1]].update(row["counts"])
        rows.append(row)
    if expected or set(votes) != {row["session"] for row in rows}:
        raise ValueError("incomplete paired sessions or unmatched semantic judgments")
    for total in totals.values():
        for outcome in ("full", "partial", "none"):
            total.setdefault(outcome, 0)
    return {"arm_totals": {arm: {"counts": total, "ratios": ratios(total)} for arm, total in totals.items()},
            "sessions": rows, "provider_usage": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("sessions", "gold", "judgments", "out"):
        parser.add_argument("--" + arg, type=Path, required=True)
    args = parser.parse_args()
    args.out.write_text(json.dumps(score(args.sessions, args.gold, args.judgments), indent=2) + "\n")
