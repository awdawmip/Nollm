from __future__ import annotations

from nollm_core import ConsistentStatePort


class SnapshotService:
    def create(self, port: ConsistentStatePort) -> bytes:
        token = port.begin_consistent_read()
        try:
            return port.export_state(token)
        finally:
            port.end_consistent_read(token)

    def restore(self, port: ConsistentStatePort, payload: bytes) -> None:
        port.import_state(payload)

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
