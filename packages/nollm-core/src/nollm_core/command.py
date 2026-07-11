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
    def __post_init__(self):
        if type(self.atom) is not MemoryAtom or type(self.target_cell) is not GeometryAddress: raise TypeError("invalid PutCommand")


@dataclass(frozen=True)
class RemoveCommand:
    handle: AtomHandle
    def __post_init__(self):
        if type(self.handle) is not AtomHandle: raise TypeError("invalid RemoveCommand")


@dataclass(frozen=True)
class ReplaceCommand:
    handle: AtomHandle
    new_payload_utf8: str
    def __post_init__(self):
        if type(self.handle) is not AtomHandle or type(self.new_payload_utf8) is not str or not self.new_payload_utf8: raise TypeError("invalid ReplaceCommand")


@dataclass(frozen=True)
class MoveCommand:
    handle: AtomHandle
    target_cell: GeometryAddress
    def __post_init__(self):
        if type(self.handle) is not AtomHandle or type(self.target_cell) is not GeometryAddress: raise TypeError("invalid MoveCommand")


@dataclass(frozen=True)
class BridgeAddCommand:
    spec: BridgeSpec
    def __post_init__(self):
        if type(self.spec) is not BridgeSpec: raise TypeError("invalid BridgeAddCommand")


@dataclass(frozen=True)
class BridgeRemoveCommand:
    bridge_id: str
    def __post_init__(self):
        if type(self.bridge_id) is not str or not self.bridge_id: raise TypeError("invalid BridgeRemoveCommand")


CoreCommand: TypeAlias = PutCommand | RemoveCommand | ReplaceCommand | MoveCommand | BridgeAddCommand | BridgeRemoveCommand
