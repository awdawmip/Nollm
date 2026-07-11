from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .atom import MemoryAtom
from .bridge import BridgeSpec
from .geometry import GeometryAddress
from .handle import AtomHandle


@dataclass(frozen=True)
class PutCommand:
    atom: MemoryAtom
    target_cell: GeometryAddress


@dataclass(frozen=True)
class RemoveCommand:
    handle: AtomHandle


@dataclass(frozen=True)
class ReplaceCommand:
    handle: AtomHandle
    new_payload_utf8: str


@dataclass(frozen=True)
class MoveCommand:
    handle: AtomHandle
    target_cell: GeometryAddress


@dataclass(frozen=True)
class BridgeAddCommand:
    spec: BridgeSpec


@dataclass(frozen=True)
class BridgeRemoveCommand:
    bridge_id: str


CoreCommand: TypeAlias = PutCommand | RemoveCommand | ReplaceCommand | MoveCommand | BridgeAddCommand | BridgeRemoveCommand
