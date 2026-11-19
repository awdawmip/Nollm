"""Reproduce the two-layer physical Coverage experiment on Nollm's own source."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

# Allows running directly from a source checkout without installing packages.
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path[:0] = [str(HERE.parent), str(REPO / "packages/nollm-core/src"), str(REPO / "packages/nollm-access/src")]

from aoci_rows import parse_volume
from records import git_tree, resolve
from nollm_core import CoreRuntime, GeometryAddress, RecallBudget, expand_physical_coverage
from nollm_access import AccessDecision, AccessRecallRequest, AccessRuntime, FileHandleStore, FileStatementStore, MemoryStatement

SOURCE_REVISION = "691590dcc6009b59a9cf51dfe7a9e7a7516eca0b"
SOURCE_VOLUME_SHA256 = "77228f86a688022b9b33ddc70155551b55578d114cc8a3b05790d1d4280f8b5c"
TOPICS = {
    "state": (0, 0, "Core runtime and durable state", "Atom commands, snapshots, storage, workspace ownership and public interfaces."),
    "geometry": (1, 0, "Physical Coverage and geometry", "Coordinates, profiles, bounded approximate quadrature, kernel registration and fixed-point arithmetic."),
    "surface": (0, 1, "Surface projection and navigation", "Aggregate occupancy, traversal budgets, local atlas and physical entry resolution."),
    "encounter": (-1, 1, "Field encounter and memory loop", "Bounded encounters, evidence capture, confirmation and durable readback."),
    "placement": (-1, 0, "Placement and revision decisions", "Write scope, action contracts, junction candidates and semantic plans."),
    "evidence": (0, -1, "Original evidence and provenance", "Statements, exact spans, formation, evidence stores and source references."),
    "recall": (1, -1, "Single-entry recall and binding", "Budgeted kernel traversal, bridges, handles and binding resolution."),
}
# The first column after the file is the host's primary responsibility. Other
# columns are intended shared contexts, independently of which cells can fit.
# This is an auditable experiment fixture, not a production semantic router.
INTENT = {
    "core": """
__init__ state geometry recall
approximate_coverage geometry surface
atom state evidence
axial geometry placement
bridge recall geometry
command state placement
compiled_templates geometry
coverage_contract geometry surface
coverage_template geometry recall
fixed_point geometry surface
geometry geometry state
handle recall state
junction placement surface
kernel_registry geometry recall surface
physical_coverage geometry surface
ports state recall
profiles geometry state
recall recall geometry
state state surface recall
storage state
surface surface geometry
validation state geometry
workspace_owner state
""",
    "access": """
__init__ encounter placement surface
cartography surface encounter
dream evidence encounter
evidence_anchor evidence
evidence_store evidence
field_encounter encounter placement
formation evidence encounter
handle_store recall evidence
locality surface placement
memory_loop encounter placement surface
placement_contract placement encounter
provenance evidence encounter
recall recall
recall_lens placement surface
runtime placement recall evidence
statement evidence recall
statement_store evidence state
surface_navigation surface recall
surface_selection surface
workspace_lock state evidence
write_policy placement
""",
}


def address(layer, q, r):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def coords(cell):
    return [cell.layer, cell.q, cell.r]


def format_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def topic_cells():
    return {key: address(-1, q, r) for key, (q, r, _, _) in TOPICS.items()}


def intent():
    result = {}
    for package, table in INTENT.items():
        for line in table.strip().splitlines():
            stem, *roles = line.split()
            path = f"packages/nollm-{package}/src/nollm_{package}/{stem}.py"
            if path in result or len(set(roles)) != len(roles) or not set(roles) <= TOPICS.keys():
                raise ValueError(f"invalid host roles for {path}")
            result[path] = roles
    return result


def placements(sites=None):
    """Fit each authored set of roles into the *actual* directional support.

    The home must reach the candidate. Prefer cells realizing the most intended
    contexts, then the fewest unintended ones, then the strongest home weight.
    More than one file can occupy a cell, each recorded once.
    """
    sites = topic_cells() if sites is None else sites
    if sites.keys() != TOPICS.keys() or set(sites.values()) != set(topic_cells().values()):
        raise ValueError("layout must assign each of the seven upper sites exactly once")
    weights = {
        key: dict(expand_physical_coverage(cell, "coverage_down").targets())
        for key, cell in sites.items()
    }
    result = {}
    for path, roles in intent().items():
        home = roles[0]
        wanted = set(roles)

        def preference(cell):
            reached = {topic for topic, members in weights.items() if cell in members}
            return -len(reached & wanted), len(reached - wanted), -weights[home][cell], cell.stable_key()

        chosen = min(weights[home], key=preference)
        result[path] = chosen
    return result


def render_row(row):
    fields = row["fields"]
    slots = " | ".join(f"{k}:{fields[k]}" for k in ("F", "R", "A", "S") if k in fields)
    tag = ".".join(row["tags"][k] for k in "ABCDE" if k in row["tags"])
    return f"{row['id'][5:]} [{tag}] {slots}"


def references(path, row, tree):
    paths = [path]
    for token in row["fields"].get("R", "-").split(","):
        token = token.strip()
        if token.startswith("code:"):
            other = token.removeprefix("code:")
            if other not in tree:
                raise ValueError(f"{path}: unresolved repository reference {other}")
            if other not in paths:
                paths.append(other)
    return tuple(f"{tree[p]}:{p}" for p in paths)


def build(repo: Path, revision: str, volume: Path, field: Path, *, sites=None):
    """Bind the pinned AOCI volume and every selected Git blob in an empty field."""
    if field.exists():
        raise FileExistsError(f"field already exists: {field}")
    rev = resolve(repo, revision)
    if rev != SOURCE_REVISION:
        raise ValueError(f"these assessments were authored for {SOURCE_REVISION}")
    tree = git_tree(repo, rev)
    actual = {p for p in tree if any(p.startswith(f"packages/nollm-{k}/src/nollm_{k}/") for k in INTENT) and p.endswith(".py")}
    sites = topic_cells() if sites is None else sites
    placement = placements(sites)
    if actual != placement.keys():
        raise ValueError(f"corpus and host placements disagree: {sorted(actual ^ placement.keys())}")
    volume_bytes = volume.read_bytes()
    volume_sha = hashlib.sha256(volume_bytes).hexdigest()
    if volume_sha != SOURCE_VOLUME_SHA256:
        raise ValueError("wrong AOCI volume bytes for the pinned self-study")
    rows = {r["id"][5:]: r for r in parse_volume(volume_bytes.decode())}
    if not actual <= rows.keys():
        raise ValueError(f"AOCI volume missing paths: {sorted(actual - rows.keys())}")
    topics = {key: {"title": t, "description": desc, "cell": coords(sites[key])} for key, (_, _, t, desc) in TOPICS.items()}
    result = {"revision": rev, "volume_sha256": volume_sha, "topics": topics, "files": {}}
    roles = intent()
    field.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=field.parent) as tmp:
        stage = Path(tmp) / "field"
        with CoreRuntime(stage) as core, AccessRuntime(core, FileStatementStore(stage), FileHandleStore(stage)) as access:
            for path in sorted(actual):
                text = render_row(rows[path])
                refs = references(path, rows[path], tree)
                stmt = MemoryStatement(f"source@{rev}:{path}", text, f"{rev}:{path}", refs)
                access.put_statement(stmt)
                access.apply(AccessDecision(
                    "place:" + stmt.statement_id, stmt.statement_id, "new", placement[path],
                    reason_text="Replay the source-reviewed Nollm self-study placement.",
                ))
                result["files"][path] = {"cell": coords(placement[path]), "topic": roles[path][0],
                                         "intent": roles[path], "text": text, "blob": tree[path]}
        (stage / "layout.json").write_text(format_json(result), encoding="utf-8")
        stage.rename(field)
    return result


def view(field: Path, manifest: dict, topic: str, mode: str):
    """Read one named origin. Owner is the same field with a single-home filter."""
    entry = address(*manifest["topics"][topic]["cell"])
    if mode == "flat":
        return [{"path": p, "score_q16": 0} for p in sorted(manifest["files"])]
    if mode not in ("coverage", "owner", "same_layer"):
        raise ValueError(f"unknown view: {mode}")
    kernel = "lateral" if mode == "same_layer" else "coverage_down"
    budget = RecallBudget(1, 8, 1, int(kernel == "lateral"), 0, len(manifest["files"]))
    if not (field / "layout.json").is_file():
        raise FileNotFoundError(field / "layout.json")
    with CoreRuntime(field) as core, AccessRuntime(core, FileStatementStore(field), FileHandleStore(field)) as access:
        recall = access.recall(AccessRecallRequest("self-study", (entry,), allowed_kernels=(kernel,), budget=budget))
        out = []
        for item in recall.items:
            if item.fallback_error:
                raise ValueError(f"unresolved source statement: {item.fallback_error}")
            stmt = access.statement_store.get(item.statement_id)
            if item.evidence_utf8 != stmt.content_utf8 or stmt.source_handle is None:
                raise ValueError(f"native evidence mismatch for {item.statement_id}")
            commit, path = stmt.source_handle.split(":", 1)
            if commit != manifest["revision"]:
                raise ValueError(f"mismatched source revision at {path}")
            if mode == "owner" and manifest["files"][path]["topic"] != topic:
                continue
            out.append({"path": path, "score_q16": item.score_q16, "cell": coords(item.handle.geometry_address),
                        "kernels": list(item.path), "text": item.evidence_utf8,
                        "source_handle": stmt.source_handle, "evidence_blobs": list(stmt.context_refs)})
        return out


def impact(manifest, path):
    """Views to revisit if this leaf changes. Compare two directional questions."""
    leaf = address(*manifest["files"][path]["cell"])
    up = dict(expand_physical_coverage(leaf, "coverage_up").targets())
    upward = {}
    downward = {}
    for topic, record in manifest["topics"].items():
        cell = address(*record["cell"])
        if cell in up:
            upward[topic] = up[cell]
        down = dict(expand_physical_coverage(cell, "coverage_down").targets())
        if leaf in down:
            downward[topic] = down[leaf]
    return {"path": path, "cell": coords(leaf), "home": manifest["files"][path]["topic"],
            "up_from_leaf_q16": upward, "down_from_entry_q16": downward}



def verify(repo, volume, field):
    """Cold-run every topic and check placement, source evidence and membership."""
    manifest = json.loads((field / "layout.json").read_text(encoding="utf-8"))
    raw = volume.read_bytes()
    if manifest["revision"] != SOURCE_REVISION or hashlib.sha256(raw).hexdigest() != SOURCE_VOLUME_SHA256:
        raise ValueError("must verify against the published source and AOCI volume")
    if manifest["volume_sha256"] != SOURCE_VOLUME_SHA256:
        raise ValueError("field was built from another volume")
    rows = {r["id"][5:]: r for r in parse_volume(raw.decode())}
    tree = git_tree(repo, SOURCE_REVISION)
    sites = {key: address(*r["cell"]) for key, r in manifest["topics"].items()}
    expected_cells = placements(sites)
    roles = intent()
    if manifest["files"].keys() != expected_cells.keys():
        raise ValueError("field manifest source set differs from authored layout")
    with CoreRuntime(field) as core:
        if core.placement_count() != len(roles) or core.bridges():
            raise ValueError("unexpected native atoms or bridges")
        occupied = set(core.occupied_cells())
        if occupied != set(expected_cells.values()):
            raise ValueError("unexpected occupied cell")
    report = {"source_files": len(roles), "occupied_layer_zero_cells": len(occupied),
              "intended_memberships": sum(map(len, roles.values())), "realized_intended": 0,
              "incidental_memberships": 0, "topics": {}}
    for topic, entry in sites.items():
        weights = dict(expand_physical_coverage(entry, "coverage_down").targets())
        expected = {p: weights[c] for p, c in expected_cells.items() if c in weights}
        native = view(field, manifest, topic, "coverage")
        measured = {item["path"]: item["score_q16"] for item in native}
        if len(measured) != len(native) or measured != expected:
            raise ValueError(f"native traversal diverged at {topic}")
        for item in native:
            path = item["path"]
            if (item["cell"] != coords(expected_cells[path]) or item["kernels"] != ["coverage_down"]
                    or item["text"] != render_row(rows[path])
                    or item["source_handle"] != f"{SOURCE_REVISION}:{path}"
                    or item["evidence_blobs"] != list(references(path, rows[path], tree))):
                raise ValueError(f"native proof did not match source at {path}")
        wanted = {p for p in roles if topic in roles[p]}
        home = {p for p in roles if topic == roles[p][0]}
        if {r["path"] for r in view(field, manifest, topic, "owner")} != home:
            raise ValueError(f"owner views disagree at {topic}")
        if view(field, manifest, topic, "same_layer"):
            raise ValueError(f"unexpected same-layer source at {topic}")
        hits = len(expected.keys() & wanted)
        spill = len(expected.keys() - wanted)
        report["topics"][topic] = {"down_files": len(expected), "owner_files": len(home),
                                   "intended_hits": hits, "incidental": spill}
        report["realized_intended"] += hits
        report["incidental_memberships"] += spill
    correct = report["realized_intended"]
    returned = correct + report["incidental_memberships"]
    report["missed_memberships"] = report["intended_memberships"] - correct
    report["membership_precision"] = correct / returned
    report["membership_recall"] = correct / report["intended_memberships"]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("build")
    create.add_argument("--repo", type=Path, default=REPO)
    create.add_argument("--rev", default=SOURCE_REVISION)
    create.add_argument("--volume", type=Path, default=HERE / "aoci/aoci.code.txt")
    create.add_argument("--field", type=Path, required=True)
    read = sub.add_parser("view")
    read.add_argument("--field", type=Path, required=True)
    read.add_argument("--topic", choices=TOPICS, required=True)
    read.add_argument("--mode", choices=("coverage", "owner", "flat", "same_layer"), default="coverage")
    change = sub.add_parser("impact")
    change.add_argument("--field", type=Path, required=True)
    change.add_argument("--path", required=True)
    confirm = sub.add_parser("verify")
    confirm.add_argument("--field", type=Path, required=True)
    confirm.add_argument("--repo", type=Path, default=REPO)
    confirm.add_argument("--volume", type=Path, default=HERE / "aoci/aoci.code.txt")
    args = parser.parse_args()
    if args.command == "build":
        manifest = build(args.repo, args.rev, args.volume, args.field)
        result = {"field": str(args.field), "revision": manifest["revision"],
                  "files": len(manifest["files"]), "topics": manifest["topics"]}
    elif args.command == "verify":
        result = verify(args.repo, args.volume, args.field)
    else:
        manifest = json.loads((args.field / "layout.json").read_text(encoding="utf-8"))
        result = view(args.field, manifest, args.topic, args.mode) if args.command == "view" else impact(manifest, args.path)
    print(format_json(result), end="")


if __name__ == "__main__":
    main()
