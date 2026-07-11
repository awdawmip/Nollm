from typing import Protocol


class ConsistentStatePort(Protocol):
    def export_state_bytes(self) -> bytes: ...

    def import_state_bytes(self, payload: bytes) -> None: ...
