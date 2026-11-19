"""Persist geometric AOCI objects in Nollm Core and Access, with no per-object label index."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import time

from nollm_access import AccessRecallRequest, AccessRuntime, FileHandleStore, FileStatementStore, HandleBinding, MemoryStatement
from nollm_core import BridgeAddCommand, BridgeSpec, CoreRuntime, GeometryAddress, GeometryAnchor, MemoryAtom, PutCommand, Q16_ONE, RecallBudget

import geocode
from aoci_rows import parse_dictionary
from geometry_cli import records_from

PITCH = 16384
PORTS = {(1, 0): "F", (0, 1): "R", (-1, 1): "A", (-1, 0): "S"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def address(q, r, layer=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def fingerprint(dictionary):
    # One binding for the shared decoder, independent of all object rows.
    return hashlib.sha256(canonical(["aoci-port-geometry-v1", PITCH, dictionary]).encode()).hexdigest()


def ref_name(q, r, value):
    if q >= 1 and r in (1, 2) and isinstance(value, str):
        return ("code:" if r == 1 else "database:") + value
    return None


def atom_key(addr):
    # Opaque identifiers depend only on physical location. They contain no ordinal
    # of a source row/column or source value. Recovery does not interpret them.
    return hashlib.sha256(canonical([addr.layer, addr.q, addr.r]).encode()).hexdigest()


def bridge(a, b):
    start, end = atom_key(a), atom_key(b)
    edge_id = hashlib.sha256((start + end).encode()).hexdigest()
    return BridgeAddCommand(BridgeSpec(edge_id, GeometryAnchor(start, (a,)),
                            GeometryAnchor(end, (b,)), Q16_ONE, "normal", 1, 1))


def prepare(shapes, dictionary):
    objects = sorted(((geocode.object_id(shape), shape) for shape in shapes), key=lambda item: item[0])
    origins = {identity: address(i * PITCH, 0) for i, (identity, _) in enumerate(objects)}
    if not objects or len(origins) != len(objects):
        raise ValueError("expected at least one object and distinct object identities")
    cells = [(address(0, 0, -1), fingerprint(dictionary))]
    bridges = []
    dangling = 0
    for identity, shape in objects:
        origin = origins[identity]
        if len({(q, r) for q, r, _ in shape}) != len(shape):
            raise ValueError("duplicate cell in encoded object")
        for q, r, value in shape:
            if not -(PITCH // 2) <= q < PITCH // 2:
                raise ValueError("object exceeds native stripe width")
            here = address(origin.q + q, r)
            cells.append((here, value))
            ref = ref_name(q,r,value)
            if ref is not None:
                if ref in origins:
                    bridges.append(bridge(here, origins[ref]))
                else:
                    dangling += 1
    return cells, bridges, dangling, len(objects)


def write_native(rows, dictionary, field):
    return write_shapes((geocode.encode(row, dictionary) for row in rows), dictionary, field)


def write_shapes(shapes, dictionary, field):
    if field.exists():
        raise FileExistsError(f"field already exists: {field}")
    started = time.perf_counter()
    cells, bridges, dangling, count = prepare(shapes, dictionary)
    commands = [PutCommand(MemoryAtom(atom_key(a), canonical(v)), a) for a,v in cells]
    field.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=field.parent) as tmp:
        stage = Path(tmp) / "field"
        with CoreRuntime(stage) as core:
            handles = core.apply_batch(tuple(commands + bridges))[:len(commands)]
            statements, bindings = FileStatementStore(stage), FileHandleStore(stage)
            with AccessRuntime(core, statements, bindings) as access:
                packed = []
                for handle, command in zip(handles, commands, strict=True):
                    atom = command.atom
                    access.put_statement(MemoryStatement(atom.atom_id, atom.payload_utf8))
                    packed.append(HandleBinding(handle, atom.atom_id))
                # Import a fresh, sorted snapshot through the versioned binding
                # store's validated public interface. The temp tree is unpublished
                # until Core, all statements and the full binding set exist.
                packed.sort(key=lambda b: (b.handle.geometry_address.stable_key(), b.handle.local_atom_id))
                snapshot = json.loads(bindings.state_bytes())
                snapshot["bindings"] = [b.to_mapping() for b in packed]
                bindings.import_state((canonical(snapshot) + "\n").encode())
                if core.placement_count() != len(cells) or len(core.bridges()) != len(bridges):
                    raise ValueError("native write count mismatch")
        stage.rename(field)
    return {"objects": count, "geometry_atoms": len(cells)-1, "shared_manifest_atoms": 1,
            "directed_bridges": len(bridges), "unresolved_reference_cells": dangling,
            "write_seconds": round(time.perf_counter()-started, 4),
            "native_bytes": sum(p.stat().st_size for p in field.rglob("*") if p.is_file())}


def check_dictionary(core, dictionary):
    meta = core.atoms_at(address(0, 0, -1))
    if len(meta) != 1 or json.loads(meta[0][1].payload_utf8) != fingerprint(dictionary):
        raise ValueError("native field does not match this schema/dictionary")


def verify_links(core, groups):
    origins = {geocode.object_id(cells): address(i*PITCH, 0) for i,cells in groups.items()}
    if len(origins) != len(groups):
        raise ValueError("duplicate decoded object identity")
    expected = {}
    for i,cells in groups.items():
        for q,r,value in cells:
            dest = origins.get(ref_name(q,r,value))
            if dest is not None:
                spec = bridge(address(i*PITCH+q,r),dest).spec
                expected[spec.bridge_id] = spec
    actual = {spec.bridge_id:spec for spec in core.bridges()}
    if actual != expected:
        raise ValueError("native reference bridge disagrees with geometric endpoints")


def read_native(field, dictionary):
    if not field.is_dir():
        raise ValueError("native field directory does not exist")
    started = time.perf_counter()
    groups = defaultdict(list)
    with CoreRuntime(field) as core, AccessRuntime(core, FileStatementStore(field), FileHandleStore(field)) as access:
        check_dictionary(core, dictionary)
        occupied = core.occupied_cells()
        entries = []
        for addr in occupied:
            items = core.atoms_at(addr)
            if len(items) != 1:
                raise ValueError("expected exactly one atom in each occupied cell")
            entries.append((addr, *items[0]))
        bindings = access.handle_store.bindings_for_handles(tuple(h for _,h,_ in entries))
        current = {b.handle:b for b in bindings}
        if len(current) != len(entries):
            raise ValueError("Core/Access binding count differs")
        for addr, handle, atom in entries:
            b = current[handle]
            statement = access.statement_store.get(b.current_statement_id)
            if (atom.atom_id != statement.statement_id or atom.payload_utf8 != statement.content_utf8 or
                    statement.source_handle is not None or statement.context_refs or b.supporting_statement_ids):
                raise ValueError("unexpected binding, payload, or auxiliary statement information")
            if addr == address(0, 0, -1):
                continue
            if addr.layer != 0:
                raise ValueError("unexpected physical layer")
            i = (addr.q + PITCH//2) // PITCH
            groups[i].append((addr.q - i*PITCH, addr.r, json.loads(statement.content_utf8)))
        rows = [geocode.decode(groups[i], dictionary) for i in sorted(groups)]
        verify_links(core, groups)
        metrics = {"objects":len(rows), "geometry_atoms":len(entries)-1, "directed_bridges":len(core.bridges()),
                   "read_seconds":round(time.perf_counter()-started,4)}
    return rows, metrics


def recall_at(access, origin, kernel):
    result = access.recall(AccessRecallRequest("geometry-probe",entry_cells=(origin,),allowed_kernels=(kernel,),
                         budget=RecallBudget(1,16,0,int(kernel=="lateral"),int(kernel=="bridge"),16)))
    if any(item.fallback_error for item in result.items):
        raise ValueError("native recall could not resolve an Access binding")
    return result.items


def named_center(core, requested):
    for a in core.occupied_cells():
        if a.layer != 0 or a.r != 0 or a.q % PITCH:
            continue
        center = core.atoms_at(a)[0][1]
        # Distinguish the two object namespaces by inspecting their own kind ray.
        code = bool(core.atoms_at(address(a.q+1,-1)))
        db = bool(core.atoms_at(address(a.q+2,-2)))
        if code == db:
            raise ValueError("invalid source-kind ray at root")
        name = ("code:" if code else "database:") + json.loads(center.payload_utf8)
        if requested is None or requested == name:
            return a, name
    raise ValueError("object not present")


def read_reference_rays(core, access, origin):
    targets = []
    ordinal = 1
    while True:
        lanes = [(r, core.atoms_at(address(origin.q + ordinal, r))) for r in (1, 2)]
        occupied = [(r, items) for r,items in lanes if items]
        if not occupied:
            break
        if len(occupied) != 1 or len(occupied[0][1]) != 1:
            raise ValueError("ambiguous physical reference lane")
        r, items = occupied[0]
        handle, atom = items[0]
        targets.append((ordinal, r, handle, atom))
        ordinal += 1
    bindings = access.handle_store.bindings_for_handles(tuple(t[2] for t in targets))
    current = {b.handle: b for b in bindings}
    values = []
    for ordinal, r, handle, atom in targets:
        if handle not in current or current[handle].current_statement_id != atom.atom_id:
            raise ValueError("unbound native reference cell")
        statement = access.statement_store.get(atom.atom_id)
        target = ref_name(ordinal, r, json.loads(statement.content_utf8))
        if target is None or atom.payload_utf8 != statement.content_utf8:
            raise ValueError("invalid reference atom")
        values.append(target)
    return values


def probe(field, dictionary, requested=None):
    if not field.is_dir():
        raise ValueError("native field directory does not exist")
    with CoreRuntime(field) as core, AccessRuntime(core, FileStatementStore(field), FileHandleStore(field)) as access:
        check_dictionary(core, dictionary)
        edges = core.bridges()
        if requested is None and edges:
            # Choose a reproducible entry with an actual link for the two-hop demonstration.
            a = edges[0].from_anchor.cells[0]
            i = (a.q + PITCH//2)//PITCH
            center = address(i*PITCH,0)
            code = bool(core.atoms_at(address(center.q+1,-1)))
            requested = ("code:" if code else "database:") + json.loads(core.atoms_at(center)[0][1].payload_utf8)
        origin, identity = named_center(core,requested)
        ports = {}
        for hit in recall_at(access, origin, "lateral"):
            a = hit.handle.geometry_address
            slot = PORTS.get((a.q-origin.q,a.r-origin.r))
            if slot and hit.path == ("lateral",):
                ports[slot]={"relative":[a.q-origin.q,a.r-origin.r],"path":list(hit.path),"value":json.loads(hit.evidence_utf8)}
        projected = {k: "-" if v["value"] is None else v["value"] for k,v in ports.items()}
        if "R" in ports and ports["R"]["value"] is None:
            targets = read_reference_rays(core, access, origin)
            if targets:
                projected["R"] = ",".join(targets)
        result = {"object":identity,"origin":[origin.q,origin.r],"ports":ports,"projected_fields":projected}
        for edge in edges:
            src = edge.from_anchor.cells[0]
            if (src.q+PITCH//2)//PITCH != origin.q//PITCH:
                continue
            witness = next((h for h in recall_at(access,src,"bridge") if h.path == ("bridge",)), None)
            if witness is None or witness.handle.geometry_address != edge.to_anchor.cells[0]:
                raise ValueError("native bridge did not resolve the target root")
            dest=witness.handle.geometry_address
            kind="code:" if core.atoms_at(address(dest.q+1,-1)) else "database:"
            result["reference"]={"relative":[src.q-origin.q,src.r],"target_root":[dest.q,dest.r],
                                 "target":kind+json.loads(witness.evidence_utf8),"path":list(witness.path)}
            break
        return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="op",required=True)
    for name in ("write","read","probe"):
        s=sub.add_parser(name)
        s.add_argument("--field",type=Path,required=True)
        spec = s.add_mutually_exclusive_group(required=True)
        spec.add_argument("--dictionary",type=Path)
        spec.add_argument("--meta",type=Path)
        s.add_argument("--out",type=Path,required=name=="read")
        if name=="write":
            payload = s.add_mutually_exclusive_group(required=True)
            payload.add_argument("--rows",type=Path)
            payload.add_argument("--geometry",type=Path)
        if name=="read":
            s.add_argument("--metrics",type=Path)
        if name=="probe":
            s.add_argument("--id")
    a=p.parse_args(argv)
    try:
        dictionary=(parse_dictionary(a.meta.read_text(encoding="utf-8")) if a.meta
                    else json.loads(a.dictionary.read_text(encoding="utf-8")))
        if a.op=="write":
            if a.geometry:
                # Reading the geometric container verifies its dictionary and checksum.
                # Any row reconstructed for validation is discarded, not used as a key.
                shapes = list(records_from(a.geometry.read_bytes(), dictionary))
                for shape in shapes:
                    geocode.validate(shape, dictionary)
                result = write_shapes(shapes, dictionary, a.field)
            else:
                result=write_native(json.loads(a.rows.read_text(encoding="utf-8")),dictionary,a.field)
        elif a.op=="read":
            result,metrics=read_native(a.field,dictionary)
            if a.metrics:
                a.metrics.write_text(canonical(metrics)+"\n",encoding="utf-8")
        else:
            result=probe(a.field,dictionary,a.id)
        if a.out:
            a.out.write_text(canonical(result)+"\n",encoding="utf-8")
        else:
            print(canonical(result))
    except (OSError, ValueError, KeyError, TypeError) as error:
        p.exit(2,f"{p.prog}: {error}\n")


if __name__=="__main__":
    main()
