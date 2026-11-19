"""Replay independent source-localization questions against the Nollm self-atlas."""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import subprocess


HERE = Path(__file__).resolve().parent
STOP = frozenset("a an and are as at be before by can do does for from how if in into is it its of on or the their to what when where which whose with without".split())


def terms(text):
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


class Index:
    """BM25 with global collection statistics, including when ranking a subset."""

    def __init__(self, docs):
        self.freq = {name: Counter(terms(doc)) for name, doc in docs.items()}
        self.length = {name: c.total() for name, c in self.freq.items()}
        self.avg = max(1, sum(self.length.values()) / len(docs))
        self.df = Counter(word for counts in self.freq.values() for word in counts)

    def scores(self, query):
        words = sorted(set(terms(query)))
        n = len(self.freq)
        idfs = {w: math.log1p((n - self.df[w] + 0.5) / (self.df[w] + 0.5)) for w in words}
        out = {}
        for name, counts in self.freq.items():
            length_weight = 1.2 * (0.25 + 0.75 * self.length[name] / self.avg)
            out[name] = sum(idfs[w] * counts[w] * 2.2 / (counts[w] + length_weight) for w in words)
        return out


def ranked(scores, candidates):
    return sorted(candidates, key=lambda path: (-scores[path], path))


def git_text(repo, rev, path):
    raw = subprocess.check_output(["git", "-C", str(repo), "show", f"{rev}:{path}"])
    return raw.decode("utf-8")


def evaluate(repo, atlas, field, fixture, token_counter):
    from vertical_atlas import view

    rev = fixture["revision"]
    if atlas["revision"] != rev:
        raise ValueError("atlas and question source revisions differ")
    notes = {p: f["text"] for p, f in atlas["files"].items()}
    sources = {p: git_text(repo, rev, p) for p in notes}
    for case in fixture["tasks"]:
        for witness in case["required"]:
            if witness["anchor"] not in sources[witness["path"]]:
                raise ValueError(f"missing witness for {case['id']}: {witness['path']}")
    topics = {k: v["title"] + "\n" + v["description"] for k, v in atlas["topics"].items()}
    topic_index, note_index = Index(topics), Index(notes)
    source_index = Index({p: p + "\n" + s for p, s in sources.items()})
    budgets = sorted({fixture["primary_file_budget"], *fixture["sensitivity_file_budgets"]})

    @lru_cache(maxsize=None)
    def local(topic, mode):
        if topic is None:
            return []
        rows = view(field, atlas, topic, mode)
        paths = [r["path"] for r in rows]
        if len(paths) != len(set(paths)) or set(paths) - set(notes):
            raise ValueError(f"invalid recall candidates for {topic}/{mode}")
        return rows

    @lru_cache(maxsize=None)
    def batch_size(paths):
        text = "\n\n".join(path + "\n" + sources[path] for path in paths)
        sizes = {"utf8_bytes": len(text.encode())}
        if token_counter:
            sizes["o200k_base_tokens"] = token_counter(text)
        return sizes

    rows = []
    totals = {}
    for case in fixture["tasks"]:
        query = case["query"]
        topic_scores = topic_index.scores(query)
        topic = ranked(topic_scores, topics)[0]
        if topic_scores[topic] == 0:
            topic = None
        src_scores, note_scores = source_index.scores(query), note_index.scores(query)
        covered = local(topic, "coverage")
        # All text-ranked arms share file-path tie breaking. Native weights are
        # examined in a separate arm so geometry cannot change reranker ties.
        arms = {
            "source_search": ranked(src_scores, sources),
            "flat_notes": ranked(note_scores, notes),
            "owner": ranked(note_scores, (r["path"] for r in local(topic, "owner"))),
            "coverage": ranked(note_scores, (r["path"] for r in covered)),
            "native_weight": [r["path"] for r in covered],
            "same_layer": ranked(note_scores, (r["path"] for r in local(topic, "same_layer"))),
        }
        for mode in ("owner", "coverage"):
            # Spend one file slot locally, then reopen global AOCI lookup.
            # This rule does not consult missing witnesses or a confidence oracle.
            arms[mode + "_then_flat"] = list(dict.fromkeys(arms[mode][:1] + arms["flat_notes"]))
        # Only now consult the expected source paths for scoring predictions.
        required = {w["path"] for w in case["required"]}
        findings = {}
        for arm, paths in arms.items():
            available = required.intersection(paths)
            findings[arm] = {
                "candidate_count": len(paths), "reachable_witnesses": sorted(available),
                "witness_ranks": [paths.index(p) + 1 if p in available else None for p in sorted(required)],
                "ranked_files": paths[:max(budgets)], "budgets": {}
            }
            for budget in budgets:
                returned = tuple(paths[:budget])
                hits = len(required.intersection(returned))
                sizes = batch_size(returned)
                findings[arm]["budgets"][str(budget)] = {"hits": hits, **sizes}
                total = totals.setdefault(arm, {}).setdefault(str(budget), Counter())
                total.update(required=len(required), hits=hits, full_tasks=int(hits == len(required)),
                             tasks=1, reachable=len(available), candidates=len(paths),
                             opened_files=len(returned), **sizes)
        rows.append(dict(id=case["id"], selected_topic=topic, required=sorted(required), arms=findings))
    return {
        "revision": rev, "files": len(sources), "topics": len(topics),
        "primary_file_budget": fixture["primary_file_budget"], "tokenizer": "o200k_base" if token_counter else None,
        "source_packet": "UTF-8: path + newline + pinned source for each returned file, joined with two newlines. Each task is an independent cold read. Covers returned text only; excludes host index processing, prompts, inference and provider usage.",
        "selection": "English BM25 (k1=1.2, b=0.75), one host-selected topic; each file index computed once on all corpus files; path tie break; zero topic score abstains. Owner/coverage share the same selected topic and file-note reranker. Native-weight arm retains native score and Core tie order. Same-layer from the empty upper cell is a reachability diagnostic. The then-flat arms take one local file and fill remaining slots with the flat note ranking, deduplicated.",
        "summary": totals, "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--field", type=Path, required=True, help="Built field containing layout.json")
    parser.add_argument("--tasks", type=Path, default=HERE / "tasks.json")
    parser.add_argument("--tokens", action="store_true", help="Count returned source packets with optional tiktoken/o200k_base")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    token_counter = None
    if args.tokens:
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")
        token_counter = lambda text: len(enc.encode_ordinary(text))
    fixture = args.tasks.read_bytes()
    manifest = (args.field / "layout.json").read_bytes()
    result = evaluate(args.repo, json.loads(manifest), args.field, json.loads(fixture), token_counter)
    result.update(tasks_sha256=sha256(fixture).hexdigest(), manifest_sha256=sha256(manifest).hexdigest())
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
