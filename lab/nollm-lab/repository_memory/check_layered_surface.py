"""Read-only check of a physically formed Surface and its adjacent descent paths.

The caller supplies the field and detail layer. This checks stored content and
actual encounter paths; it does not choose semantic entries or measure answer
quality. It uses only public Core/Access contracts and the shared encounter API.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"),
               str(ROOT / "packages/nollm-access/src"), str(Path(__file__).parent)]
from nollm_core import CoreRuntime, expand_physical_coverage
from nollm_access import FileHandleStore, FileStatementStore
from coverage_cli import address, coords
from project_memory import encounter


def visible_bytes(page):
    return len(json.dumps({k:v for k,v in page.items() if k != "cursor"},
                          ensure_ascii=False,separators=(",",":")).encode())


def check(field, detail_layer=0):
    field = Path(field).resolve()
    original_get, original_read = FileStatementStore.get, Path.read_bytes
    reads, io = [], []
    def tracked_get(store, identity):
        statement = original_get(store, identity)
        reads.append({"id":identity,"utf8_bytes":len(statement.content_utf8.encode())})
        return statement
    def tracked_read(path):
        data = original_read(path)
        if path in (field / "core/current_state.json", field / "access/bindings.json"):
            io.append({"path":str(path.relative_to(field)),"bytes":len(data)})
        return data
    with patch.object(FileStatementStore,"get",tracked_get), patch.object(Path,"read_bytes",tracked_read):
        first = encounter(field)
    if first["kind"] != "surface" or first["has_more"]:
        raise ValueError("this formed-Surface check expects one complete first page")
    if any(c["truncated"] or c["text_truncated"] for c in first["candidates"]):
        raise ValueError("formed Surface omitted or clipped stored content")
    with CoreRuntime(field) as core:
        cells = core.occupied_cells()
        handles = [h for c in cells for h,_ in core.atoms_at(c)]
        atoms = {h:a for c in cells for h,a in core.atoms_at(c)}
        bridges = len(core.bridges())
    bindings = FileHandleStore(field).bindings_for_handles(tuple(handles))
    current = {b.current_statement_id:b.handle for b in bindings}
    layer_stats = defaultdict(lambda:{"cells":0,"statements":0,"utf8_bytes":0})
    for cell in cells:
        layer_stats[cell.layer]["cells"] += 1
    for identity,handle in current.items():
        stats = layer_stats[handle.geometry_address.layer]
        stats["statements"] += 1
        stats["utf8_bytes"] += len(atoms[handle].payload_utf8.encode())
    if any(current[item["id"]].geometry_address.layer not in first["surface_layers"] for item in reads):
        raise ValueError("first Surface read a deeper current statement body")
    previews = [body for cell in first["candidates"] for body in cell["previews"]]
    expected = [atoms[h].payload_utf8 for h in current.values()
                if h.geometry_address.layer in first["surface_layers"]]
    if sorted(previews) != sorted(expected):
        raise ValueError("first Surface text differs from complete stored upper bodies")
    paths = defaultdict(list)
    roots, locality_sizes = [], []
    for shown in first["candidates"]:
        physical = encounter(field,(shown["id"],),cursor=first["cursor"])
        for candidate in physical["candidates"]:
            if not candidate["native_atoms"]:
                continue
            local = encounter(field,(candidate["id"],),cursor=physical["cursor"])
            root = local["entry"]
            roots.append({"entry":root,"text":candidate["previews"],
                          "first_local_layers":sorted({x["cell"][0] for x in local["items"]})})
            locality_sizes.append(visible_bytes(local))
            if any(item["cell"][0] > root[0]+1 for item in local["items"]):
                raise ValueError("first selected locality eagerly returned distant detail")
            pending = [local]
            visited = set()
            while pending:
                page = pending.pop()
                focus = tuple(page["focus"])
                if focus in visited:
                    continue
                visited.add(focus)
                if page["entry"] != root:
                    raise ValueError("descent changed the original physical entry")
                for item in page["items"]:
                    if item["cell"][0] != detail_layer:
                        continue
                    if item["text"] != atoms[current[item["id"]]].payload_utf8:
                        raise ValueError("returned detail differs from its current stored body")
                    path = [*page["focus_path"]]
                    if item["cell"] != path[-1]:
                        path.append(item["cell"])
                    if path not in paths[item["id"]]:
                        paths[item["id"]].append(path)
                if focus[0] >= detail_layer-1:
                    continue
                for target in page["descent_candidates"]:
                    if target["native_atoms"]:
                        child = encounter(field,cursor=page["cursor"],descend=target["id"])
                        locality_sizes.append(visible_bytes(child))
                        pending.append(child)
    expected_details = {i for i,h in current.items() if h.geometry_address.layer == detail_layer}
    missing = sorted(expected_details-paths.keys())
    # Concrete witness: up support is not the inverse of the reading direction.
    upper, lower = address(-1,-11,9), address(0,-9,13)
    hit = next(m for m in expand_physical_coverage(upper,"coverage_down").members if m.target == lower)
    reverse = expand_physical_coverage(lower,"coverage_up")
    asymmetric = upper not in {m.target for m in reverse.members}
    assert hit.hit_count == 1 and asymmetric
    return {
        "surface_complete":True,"surface_body_utf8_bytes":sum(len(x.encode()) for x in previews),
        "surface_visible_json_utf8_bytes":visible_bytes(first),"surface_statement_reads":reads,
        "first_surface_core_binding_reads":io,"layer_stats":dict(sorted(layer_stats.items())),
        "detail_statements":len(expected_details),"details_returned":len(paths),"missing_details":missing,
        "details_with_multiple_upper_entries":sum(len({tuple(p[0]) for p in ps}) > 1 for ps in paths.values()),
        "paths":dict(paths),"roots":roots,"existing_bridges":bridges,
        "locality_visible_json_max_bytes":max(locality_sizes,default=0),
        "down_not_reverse_up_witness":{"upper":coords(upper),"lower":coords(lower),"down_hits":hit.hit_count,
                                      "up_contains_upper":not asymmetric},
        "scope":"Native path and content evidence; semantic decisions and physical page I/O require separate evaluation",
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field",type=Path,required=True)
    parser.add_argument("--detail-layer",type=int,default=0)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=check(args.field,args.detail_layer)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in {"paths","roots","surface_statement_reads"}},
                     ensure_ascii=False,indent=2))
    if result["missing_details"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
