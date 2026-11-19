"""Compile AOCI code volumes into geometric records and query their coordinates."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from struct import Struct
import sys
from tempfile import NamedTemporaryFile

from aoci_rows import parse_dictionary, parse_volume, render_volume
from geocode import (
    decode, dictionary_digest, encode, field_value, match_axis, object_id,
    pack, relation_targets, unpack, validate,
)


MAGIC = b"NLGV1\0"
SIZE = Struct(">I")


def encode_volume(rows, dictionary):
    output = bytearray(MAGIC)
    output.extend(bytes.fromhex(dictionary_digest(dictionary)))
    output.extend(SIZE.pack(len(rows)))
    seen = set()
    for row in rows:
        if row["id"] in seen:
            raise ValueError(f"duplicate object {row['id']}")
        seen.add(row["id"])
        record = pack(encode(row, dictionary))
        output.extend(SIZE.pack(len(record)))
        output.extend(record)
    return bytes(output) + sha256(output).digest()


def records_from(data, dictionary):
    header_size = len(MAGIC) + 32
    if len(data) < header_size + SIZE.size + 32 or not data.startswith(MAGIC):
        raise ValueError("unrecognized geometric volume")
    if sha256(data[:-32]).digest() != data[-32:]:
        raise ValueError("volume checksum mismatch")
    if data[len(MAGIC):header_size] != bytes.fromhex(dictionary_digest(dictionary)):
        raise ValueError("volume and tag dictionary disagree")
    count, = SIZE.unpack_from(data, header_size)
    offset = header_size + SIZE.size
    end = len(data) - 32
    seen = set()
    for _ in range(count):
        if offset + SIZE.size > end:
            raise ValueError("truncated record header")
        length, = SIZE.unpack_from(data, offset)
        offset += SIZE.size
        if offset + length > end:
            raise ValueError("truncated geometric record")
        cells = unpack(data[offset:offset + length])
        offset += length
        key = object_id(cells)
        if key in seen:
            raise ValueError(f"duplicate object {key}")
        seen.add(key)
        yield cells
    if offset != end:
        raise ValueError("unconsumed geometric records")


def axis_eq(value):
    axis, separator, code = value.partition("=")
    if axis not in {"A", "B", "C", "D", "E"} or not separator or not code:
        raise argparse.ArgumentTypeError("give a tag axis and value, for example C=7")
    return axis, code


def select(records, dictionary, args):
    if args.limit < 0:
        raise ValueError("limit must be nonnegative")
    constraints = [(axis, "eq", value) for axis, value in args.axis]
    if args.min_importance is not None:
        constraints.append(("C", "gte", str(args.min_importance)))
    if args.feature_state is not None:
        constraints.append(("D", args.feature_state, None))
    result = []
    total = 0
    for cells in records:
        key = object_id(cells)
        if args.id is not None and args.id != key:
            continue
        if not all(match_axis(cells, dictionary, axis, op, value) for axis, op, value in constraints):
            continue
        if args.target is not None and args.target not in relation_targets(cells):
            continue
        total += 1
        if len(result) < args.limit:
            item = {"id": key}
            if args.field is not None:
                item["value"] = field_value(cells, args.field)
            result.append(item)
    return {"matched": total, "items": result}


def write_output(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        try:
            handle.write(data)
            handle.close()
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("encode", "decode", "query", "check"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--meta", required=True, type=Path, help="AOCI metadata volume containing its tag dictionaries")
        if name == "encode":
            cmd.add_argument("--volume", required=True, type=Path)
        else:
            cmd.add_argument("--geometry", required=True, type=Path)
        cmd.add_argument("--out", type=Path, required=name == "encode")
        if name == "query":
            cmd.add_argument("--axis", type=axis_eq, action="append", default=[], help="repeat a tag constraint, such as C=7")
            cmd.add_argument("--min-importance", type=int, help="select positions for C at or above this score")
            cmd.add_argument("--feature-state", choices=["present", "missing"], help="filter on presence of an optional D tag")
            cmd.add_argument("--id", help="exact code object identity")
            cmd.add_argument("--target", help="exact target in a recognized relation list")
            cmd.add_argument("--field", choices=["F","R","A","S"], help="read the value from its geometric slot")
            cmd.add_argument("--limit", type=int, default=20)
        if name == "decode":
            cmd.add_argument("--format", choices=["volume", "json"], default="volume")
    args = parser.parse_args(argv)
    try:
        input_path = args.volume if args.command == "encode" else args.geometry
        if args.out is not None and args.out.resolve() in {input_path.resolve(), args.meta.resolve()}:
            raise ValueError("choose an output distinct from the inputs")
        dictionary = parse_dictionary(args.meta.read_text(encoding="utf-8"))
        if args.command == "encode":
            rows = parse_volume(args.volume.read_text(encoding="utf-8"))
            data = encode_volume(rows, dictionary)
        else:
            records = records_from(input_path.read_bytes(), dictionary)
            if args.command == "check":
                count = 0
                for cells in records:
                    validate(cells, dictionary)
                    count += 1
                result = {"valid": count}
            elif args.command == "query":
                result = select(records, dictionary, args)
            else:
                result = [decode(cells, dictionary) for cells in records]
            if args.command == "decode" and args.format == "volume":
                data = render_volume(result).encode("utf-8")
            else:
                data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if args.out:
            write_output(args.out, data)
        else:
            sys.stdout.buffer.write(data)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")


if __name__ == "__main__":
    main()
