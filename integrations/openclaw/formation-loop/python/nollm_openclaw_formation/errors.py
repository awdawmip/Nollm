from __future__ import annotations


class FormationAdapterError(ValueError):
    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category
