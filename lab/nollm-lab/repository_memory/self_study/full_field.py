"""File the complete pinned Nollm AOCI project volume into one native workspace."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import vertical_atlas as atlas
from nollm_access import AccessDecision, AccessRecallRequest, AccessRuntime, FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime, RecallBudget, expand_physical_coverage

# Codex-authored filing scopes. Longer prefixes precede their enclosing family.
# Within each scope, the filename order alone partitions the pages.
SCOPES = (
    ("reference/python/nollm/dream_geometry/", "reference-dream-geometry"),
    ("reference/python/nollm/grf/", "reference-grf"),
    ("reference/python/nollm/", "reference-model"),
    ("reference/python/tests/", "reference-tests"),
    ("reference/python/scripts/", "reference-scripts"),
    ("reference/", "reference-project"),
    ("integrations/openclaw/nollm-memory-provider/", "openclaw-provider"),
    ("integrations/openclaw/formation-loop/", "openclaw-formation"),
    ("integrations/openclaw/", "openclaw-adapters"),
    ("integrations/", "other-host-adapters"),
    ("lab/nollm-lab/repository_memory/", "repository-memory-lab"),
    ("lab/nollm-lab/geometry/", "geometry-lab"),
    ("lab/", "other-labs"),
    ("packages/nollm-core/", "core-package"),
    ("packages/nollm-access/", "access-package"),
    ("packages/", "other-packages"),
    ("protocol/v2/", "protocol-v2"),
    ("protocol/v3/", "protocol-v3"),
    ("protocol/", "protocol"),
    ("docs/architecture/", "architecture-documents"),
    ("docs/project/", "project-documents"),
    ("distributions/", "distributions"),
    ("experiments/", "experiments"),
    ("cortex/", "cortex"),
    ("tools/", "project-tooling"),
    ("", "repository-root-and-policy"),
)
ROOM_SIZE = 8
FIELD_SCHEMA = "nollm-self-project-field-v1"
VOLUME = atlas.HERE / "aoci/aoci.code.txt"


def layout(paths):
    paths = set(paths)
    placed = atlas.placements()
    if not placed.keys() <= paths:
        raise ValueError("missing controlled Core/Access sources")
    rooms = {
        "runtime/" + key: {"scope": "runtime", "entry": atlas.coords(site), "title": atlas.TOPICS[key][2]}
        for key, site in atlas.topic_cells().items()
    }
    used = {cell for site in atlas.topic_cells().values() for cell, _ in expand_physical_coverage(site, "coverage_down").targets()}
    groups = defaultdict(list)
    for p in sorted(paths - placed.keys()):
        scope = next(label for prefix, label in SCOPES if p.startswith(prefix))
        groups[scope].append(p)
    for index, (_, scope) in enumerate(SCOPES):
        files = groups[scope]
        for start in range(0, len(files), ROOM_SIZE):
            number = start // ROOM_SIZE
            # Disjoint pages on the same patch for one source family. Native
            # layer transforms are evaluated independently for each coordinate.
            site = atlas.address(-1, 128 * (1 + index) + 5 * (number % 8), 5 * (number // 8))
            weights = dict(expand_physical_coverage(site, "coverage_down").targets())
            cells = sorted(weights, key=lambda c: (-weights[c], c.stable_key()))
            if used.intersection(cells):
                raise ValueError(f"overlapping filing pages at {scope}/{number + 1}")
            used.update(cells)
            page = files[start:start + ROOM_SIZE]
            for i, path in enumerate(page):
                placed[path] = cells[i % len(cells)]
            rooms[f"{scope}/{number + 1:02d}"] = {"scope": scope, "entry": atlas.coords(site), "first": page[0],
                                                 "last": page[-1], "count": len(page)}
    return placed, rooms


def inputs(repo, volume):
    raw = volume.read_bytes()
    if hashlib.sha256(raw).hexdigest() != atlas.SOURCE_VOLUME_SHA256:
        raise ValueError("wrong AOCI volume for the pinned project study")
    rows = {r["id"][5:]: r for r in atlas.parse_volume(raw.decode())}
    tree = atlas.git_tree(repo, atlas.SOURCE_REVISION)
    if not rows.keys() <= tree.keys():
        raise ValueError("volume cites absent source files")
    return rows, tree


def build(repo, volume, field):
    if field.exists():
        raise FileExistsError(f"field already exists: {field}")
    rows, tree = inputs(repo, volume)
    placed, rooms = layout(rows)
    manifest = {"schema": FIELD_SCHEMA, "revision": atlas.SOURCE_REVISION, "volume_sha256": atlas.SOURCE_VOLUME_SHA256,
                "files": len(rows), "room_size": ROOM_SIZE, "rooms": rooms}
    field.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=field.parent) as temporary:
        stage = Path(temporary) / "field"
        with CoreRuntime(stage) as core, AccessRuntime(core, FileStatementStore(stage), FileHandleStore(stage)) as access:
            for p, row in sorted(rows.items()):
                rev = atlas.SOURCE_REVISION
                stmt = MemoryStatement("source@" + rev + ":" + p, atlas.render_row(row),
                                       rev + ":" + p, atlas.references(p, row, tree))
                access.put_statement(stmt)
                access.apply(AccessDecision("file:" + stmt.statement_id, stmt.statement_id, "new", placed[p],
                                            reason_text="File the reviewed project AOCI object at its layer-zero site."))
        (stage / "rooms.json").write_text(atlas.format_json(manifest), encoding="utf-8")
        stage.rename(field)
    return manifest


def read(access, room):
    """One empty upper entry, one native down step, read back Access evidence."""
    entry = atlas.address(*room["entry"])
    limit = 44 if room["scope"] == "runtime" else ROOM_SIZE
    found = access.recall(AccessRecallRequest("project-room", (entry,), allowed_kernels=("coverage_down",),
                                               budget=RecallBudget(1, 8, 1, 0, 0, limit)))
    records = []
    for item in found.items:
        if item.fallback_error:
            raise ValueError(f"unbound statement: {item.fallback_error}")
        stmt = access.statement_store.get(item.statement_id)
        if item.path != ("coverage_down",) or item.evidence_utf8 != stmt.content_utf8 or not stmt.source_handle:
            raise ValueError(f"unexpected native result: {item.statement_id}")
        rev, path = stmt.source_handle.split(":", 1)
        if rev != atlas.SOURCE_REVISION:
            raise ValueError(f"wrong revision for {path}")
        records.append({"path": path, "score_q16": item.score_q16, "cell": atlas.coords(item.handle.geometry_address),
                        "kernels": list(item.path), "text": item.evidence_utf8, "source_handle": stmt.source_handle,
                        "evidence_blobs": list(stmt.context_refs)})
    return records


def open_manifest(field):
    manifest = json.loads((field / "rooms.json").read_text(encoding="utf-8"))
    if (manifest["schema"], manifest["revision"], manifest["volume_sha256"]) != (
            FIELD_SCHEMA, atlas.SOURCE_REVISION, atlas.SOURCE_VOLUME_SHA256):
        raise ValueError("wrong native field or study version")
    return manifest


def verify(repo, volume, field):
    rows, tree = inputs(repo, volume)
    placed, rooms = layout(rows)
    if rooms != open_manifest(field)["rooms"]:
        raise ValueError("published room directory differs from the pinned layout")
    by_cell = defaultdict(set)
    for p, cell in placed.items():
        by_cell[cell].add(p)
    reached = set()
    counts = {}
    scope_counts = Counter()
    with CoreRuntime(field) as core, AccessRuntime(core, FileStatementStore(field), FileHandleStore(field)) as access:
        if core.placement_count() != len(placed) or core.bridges() or set(core.occupied_cells()) != by_cell.keys():
            raise ValueError("native placement count, occupancy or bridges diverged")
        for name, room in rooms.items():
            weights = dict(expand_physical_coverage(atlas.address(*room["entry"]), "coverage_down").targets())
            expected = {p for cell in weights for p in by_cell.get(cell, ())}
            found = read(access, room)
            if {r["path"] for r in found} != expected or len(found) != len(expected):
                raise ValueError(f"native membership differs at {name}")
            for item in found:
                p = item["path"]
                if (item["score_q16"] != weights[placed[p]] or item["cell"] != atlas.coords(placed[p])
                        or item["text"] != atlas.render_row(rows[p])
                        or item["evidence_blobs"] != list(atlas.references(p, rows[p], tree))):
                    raise ValueError(f"native source or score differs for {p}")
            reached.update(expected)
            counts[name] = len(found)
            scope_counts[room["scope"]] += 1
    if reached != rows.keys():
        raise ValueError("room readback did not recover the complete volume")
    filed = [n for name, n in counts.items() if rooms[name]["scope"] != "runtime"]
    return {"revision": atlas.SOURCE_REVISION, "volume_sha256": atlas.SOURCE_VOLUME_SHA256,
            "unique_source_atoms": len(reached), "occupied_layer_zero_cells": len(by_cell), "rooms": len(rooms),
            "room_counts_by_scope": dict(sorted(scope_counts.items())), "filing_pages": len(filed),
            "filing_page_min": min(filed), "filing_page_max": max(filed),
            "controlled_view_counts": {n: c for n, c in counts.items() if rooms[n]["scope"] == "runtime"},
            "total_native_readbacks": sum(counts.values())}


def main():
    cmd = argparse.ArgumentParser(description=__doc__)
    sub = cmd.add_subparsers(dest="command", required=True)
    for name in ("build", "verify", "rooms", "read"):
        mode = sub.add_parser(name)
        mode.add_argument("--field", type=Path, required=True)
        if name in ("build", "verify"):
            mode.add_argument("--repo", type=Path, default=atlas.REPO)
            mode.add_argument("--volume", type=Path, default=VOLUME)
        if name == "read":
            mode.add_argument("--room", required=True)
        if name == "rooms":
            mode.add_argument("--scope")
    args = cmd.parse_args()
    if args.command == "build":
        manifest = build(args.repo, args.volume, args.field)
        out = {"field": str(args.field), "files": manifest["files"], "rooms": len(manifest["rooms"])}
    elif args.command == "verify":
        out = verify(args.repo, args.volume, args.field)
    else:
        rooms = open_manifest(args.field)["rooms"]
        if args.command == "rooms":
            out = {k: r for k, r in rooms.items() if args.scope is None or r["scope"] == args.scope}
        else:
            if args.room not in rooms:
                cmd.error(f"unknown room {args.room!r}")
            with CoreRuntime(args.field) as core, AccessRuntime(core, FileStatementStore(args.field), FileHandleStore(args.field)) as access:
                out = read(access, rooms[args.room])
    print(atlas.format_json(out), end="")


if __name__ == "__main__":
    main()
