from __future__ import annotations

from .ports import ConsistentStatePort


class SnapshotService:
    def create(self, port: ConsistentStatePort) -> bytes:
        return port.export_state_bytes()

    def restore(self, port: ConsistentStatePort, payload: bytes) -> None:
        port.import_state_bytes(payload)

    def clone(
        self,
        source: ConsistentStatePort,
        target: ConsistentStatePort,
    ) -> bytes:
        payload = self.create(source)
        self.restore(target, payload)
        return payload

    def verify(self, port: ConsistentStatePort, expected: bytes) -> bool:
        return self.create(port) == expected

    def structural_diff(self, left: bytes, right: bytes) -> bool:
        return left != right
