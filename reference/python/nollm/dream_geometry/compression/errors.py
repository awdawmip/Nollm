"""DG5 structured compression errors."""

from __future__ import annotations


class CompressionPlanningError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(f"{reason_code}: {message}")
        self.reason_code = reason_code
