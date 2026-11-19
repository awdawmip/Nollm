"""Reversible relative hex-cell representation of normalized AOCI code/database objects.

A shape is an iterable of (axial q, axial r, payload) triples. An occupied cell
may carry no text (None), an explicitly empty UTF-8 string, or literal content.
The shared ordered tag dictionary is supplied by the caller.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
import json
import re
import struct
from types import MappingProxyType
import zlib


RAYS = {"A": (1, 0), "B": (0, 1), "C": (-1, 1), "D": (-1, 0), "E": (0, -1)}
PORTS = {"F": (1, 0), "R": (0, 1), "A": (-1, 1), "S": (-1, 0)}
KINDS = ("code", "database")
MAGIC = b"NGS\x01"
MAX_RADIUS = (1 << 31) - 1


def _check_dictionary(dictionary):
    if not isinstance(dictionary, Mapping) or set(dictionary) != set(RAYS):
        raise ValueError("expected five ordered axis dictionaries")
    for axis in RAYS:
        symbols = dictionary[axis]
        if not isinstance(symbols, (list, tuple)) or not all(isinstance(x, str) and x for x in symbols):
            raise ValueError("dictionary entries must be nonempty strings in an ordered list")
        if len(symbols) != len(set(symbols)) or (axis != "D" and not symbols):
            raise ValueError("duplicate dictionary symbol or missing required axis")


def dictionary_digest(dictionary):
    _check_dictionary(dictionary)
    data = json.dumps(dictionary, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return sha256(data.encode("utf-8")).hexdigest()


def _identity(value):
    if not isinstance(value, str):
        raise ValueError("expected an object identity")
    kind, sep, path = value.partition(":")
    if not sep or kind not in KINDS or not path:
        raise ValueError("expected a code: or database: object identity with a name")
    return kind, path


def _typed_list(value):
    """Only lift references when joining their canonical spellings is lossless."""
    refs = []
    for token in value.split(","):
        try:
            kind, path = _identity(token)
        except ValueError:
            return []
        if path.strip() != path or any(c.isspace() for c in path):
            return []
        refs.append((kind, path))
    return refs


@dataclass(frozen=True)
class _CompiledShape:
    """Read-only coordinate lookup, with no decoded axes or role fields."""
    positions: Mapping


def compiled_cells(cells, dictionary):
    """Validate once for repeated coordinate probes in the same dictionary."""
    board = MappingProxyType(dict(_board(cells)))
    result = _CompiledShape(board)
    validate(result, dictionary)
    return result


def _board(cells):
    if isinstance(cells, _CompiledShape):
        return cells.positions
    board = {}
    for cell in cells:
        if not isinstance(cell, (list, tuple)) or len(cell) != 3:
            raise ValueError("expected coordinate and payload triples")
        q, r, value = cell
        if type(q) is not int or type(r) is not int or max(abs(q), abs(r), abs(q + r)) > MAX_RADIUS:
            raise ValueError("invalid hex coordinate")
        if value is not None and not isinstance(value, str):
            raise ValueError("payload must be text or None")
        if (q, r) in board:
            raise ValueError("duplicate occupied cell")
        board[q, r] = value
    return board


def _sorted_cells(board):
    return [(q, r, board[q, r]) for q, r in sorted(board)]


def encode(row, dictionary):
    """Replace every per-object role/axis name and category value with geometry."""
    _check_dictionary(dictionary)
    if not isinstance(row, Mapping) or set(row) != {"id", "tags", "fields"}:
        raise ValueError("expected an id, tags and fields")
    tags, fields = row["tags"], row["fields"]
    if not isinstance(tags, Mapping) or not {"A", "B", "C", "E"} <= set(tags) <= set(RAYS):
        raise ValueError("missing required tag axis or unknown axis")
    if not isinstance(fields, Mapping) or not set(fields) <= set(PORTS):
        raise ValueError("unknown field")
    kind, path = _identity(row["id"])
    kind_radius = 1 + KINDS.index(kind)
    board = {(0, 0): path, (kind_radius, -kind_radius): None}
    for axis, symbol in tags.items():
        if symbol not in dictionary[axis]:
            raise ValueError(f"unregistered symbol for axis {axis}")
        radius = 2 + dictionary[axis].index(symbol)
        q, r = RAYS[axis]
        board[radius * q, radius * r] = None
    for role, value in fields.items():
        if not isinstance(value, str):
            raise ValueError("field contents must be strings")
        refs = _typed_list(value) if role == "R" else []
        board[PORTS[role]] = None if refs or value == "-" else value
        for ordinal, (target_kind, target) in enumerate(refs, 1):
            board[ordinal, 1 + KINDS.index(target_kind)] = target
    return _sorted_cells(board)


def _object_id(board):
    path = board.get((0, 0))
    if not isinstance(path, str) or not path:
        raise ValueError("missing or empty object origin")
    selected = [k for i, k in enumerate(KINDS, 1) if (i, -i) in board]
    if len(selected) != 1:
        raise ValueError("missing or ambiguous identity direction")
    return selected[0] + ":" + path


def object_id(cells):
    return _object_id(_board(cells))


def _axis_radius(board, dictionary, axis):
    if axis not in RAYS:
        raise ValueError("unknown axis")
    q, r = RAYS[axis]
    ranks = [i for i in range(len(dictionary[axis])) if ((i+2)*q, (i+2)*r) in board]
    if len(ranks) > 1:
        raise ValueError(f"ambiguous axis {axis}")
    return ranks[0] if ranks else None


def axis_value(cells, dictionary, axis):
    index = _axis_radius(_board(cells), dictionary, axis)
    return None if index is None else dictionary[axis][index]


def match_axis(cells, dictionary, axis, op, value=None):
    """Test coordinate occupancy directly; there is no per-object tag-string parser."""
    if axis not in RAYS:
        raise ValueError("unknown axis")
    board = _board(cells)
    labels = dictionary[axis]
    q, r = RAYS[axis]
    if op in ("present", "missing"):
        exists = any(((i+2)*q, (i+2)*r) in board for i in range(len(labels)))
        return (not exists) if op == "missing" or value is False else exists
    if op not in ("eq", "gte"):
        raise ValueError("expected eq, gte, present or missing")
    if type(value) not in (str, int):
        return False
    wanted = str(value)
    if op == "eq":
        ranks = (i for i, symbol in enumerate(labels) if symbol.casefold() == wanted.casefold())
    elif axis == "C":
        # Unlisted thresholds (e.g. C >= 6) are valid AOCI predicates.
        if not re.fullmatch(r"[+-]?[0-9]+", wanted):
            return False
        ranks = (i for i, symbol in enumerate(labels)
                 if re.fullmatch(r"[+-]?[0-9]+", symbol) and int(symbol) >= int(wanted))
    elif axis == "E" and set(labels) == set("TSML") and wanted.upper() in tuple("TSML"):
        # Physical scale range over the standard four symbols, an extension
        # to AOCI's C-only numeric threshold.
        ranks = (i for i, symbol in enumerate(labels)
                 if "TSML".index(symbol) >= "TSML".index(wanted.upper()))
    else:
        raise ValueError("range filtering requires C or the standard E scale")
    return any(((i+2)*q, (i+2)*r) in board for i in ranks)


def _targets(board):
    slots = {}
    for (q, r), name in board.items():
        if q >= 1 and 1 <= r <= len(KINDS):
            if q in slots or not isinstance(name, str) or not name:
                raise ValueError("ambiguous or empty reference target")
            slots[q] = KINDS[r-1] + ":" + name
    if set(slots) != set(range(1, len(slots)+1)):
        raise ValueError("broken reference sequence")
    return [slots[i] for i in range(1, len(slots)+1)]


def relation_targets(cells):
    """Read ordered, explicitly typed outgoing references from positive-quadrant cells."""
    return _targets(_board(cells))


def _field(board, role):
    position = PORTS[role]
    if position not in board:
        return None
    value = board[position]
    if role == "R":
        targets = _targets(board)
        if targets:
            if value is not None:
                raise ValueError("both literal and geometric relationship content")
            return ",".join(targets)
    return "-" if value is None else value


def field_value(cells, role):
    if role not in PORTS:
        raise ValueError("unknown field role")
    return _field(_board(cells), role)


def decode(cells, dictionary):
    """Recover normalized semantics and reject stray, ambiguous or noncanonical cells."""
    _check_dictionary(dictionary)
    board = _board(cells)
    tags = {}
    for axis in RAYS:
        index = _axis_radius(board, dictionary, axis)
        if index is not None:
            tags[axis] = dictionary[axis][index]
    fields = {role: _field(board, role) for role, point in PORTS.items() if point in board}
    result = {"id": _object_id(board), "tags": tags, "fields": fields}
    if encode(result, dictionary) != _sorted_cells(board):
        raise ValueError("unexpected cell, payload or noncanonical representation")
    return result


def validate(cells, dictionary):
    decode(cells, dictionary)


def _varint(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return result


def _read_int(data, pos):
    result = 0
    for shift in range(0, 64, 7):
        if pos == len(data):
            raise ValueError("truncated integer")
        byte = data[pos]
        pos += 1
        result |= (byte & 127) << shift
        if byte < 128:
            if shift and byte == 0:
                raise ValueError("noncanonical integer")
            return result, pos
    raise ValueError("oversized integer")


def pack(cells):
    """Serialize sorted cells, using zigzag integers and a frame checksum."""
    canonical = _sorted_cells(_board(cells))
    result = bytearray(MAGIC)
    result.extend(_varint(len(canonical)))
    for q, r, value in canonical:
        for n in (q, r):
            result.extend(_varint(2*n if n >= 0 else -2*n-1))
        if value is None:
            result.append(0)
        else:
            raw = value.encode("utf-8")
            result.extend(_varint(1 + len(raw)))
            result.extend(raw)
    result.extend(struct.pack(">I", zlib.crc32(result)))
    return bytes(result)


def unpack(data):
    if len(data) < len(MAGIC)+5 or not data.startswith(MAGIC):
        raise ValueError("unknown shape frame format")
    body = data[:-4]
    if struct.unpack(">I", data[-4:])[0] != zlib.crc32(body):
        raise ValueError("shape frame checksum mismatch")
    size, pos = _read_int(body, len(MAGIC))
    if size > (len(body)-pos)//3:
        raise ValueError("invalid shape cell count")
    cells = []
    for _ in range(size):
        uq, pos = _read_int(body, pos)
        ur, pos = _read_int(body, pos)
        length, pos = _read_int(body, pos)
        q = (uq >> 1) ^ -(uq & 1)
        r = (ur >> 1) ^ -(ur & 1)
        value = None
        if length:
            end = pos + length - 1
            if end > len(body):
                raise ValueError("truncated payload")
            value = body[pos:end].decode("utf-8")
            pos = end
        cells.append((q, r, value))
    if pos != len(body) or cells != _sorted_cells(_board(cells)):
        raise ValueError("trailing bytes or noncanonical cell order")
    return cells
