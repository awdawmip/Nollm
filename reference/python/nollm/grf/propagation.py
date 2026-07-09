"""Sparse integer activation propagation for GRF recall."""

from __future__ import annotations

from dataclasses import dataclass

from .cell_address import CellAddress
from .fixed_point import Q16_ONE, q16_mul


@dataclass(frozen=True, order=True)
class SparseActivation:
    cell: CellAddress
    score_q16: int
    path_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.cell, CellAddress):
            raise TypeError("cell must be CellAddress")
        if type(self.score_q16) is not int or self.score_q16 < 0 or self.score_q16 > Q16_ONE:
            raise ValueError("score_q16 must be Q16 integer")
        if not isinstance(self.path_id, str) or self.path_id == "":
            raise ValueError("path_id must be non-empty text")


@dataclass(frozen=True)
class ActivationFrontier:
    step: int
    activations: tuple[SparseActivation, ...]

    def __post_init__(self) -> None:
        if type(self.step) is not int or self.step < 0:
            raise ValueError("step must be non-negative integer")
        if any(not isinstance(item, SparseActivation) for item in self.activations):
            raise TypeError("activations must be SparseActivation")

    def merged(self, beam: int) -> "ActivationFrontier":
        if type(beam) is not int or beam < 1:
            raise ValueError("beam must be positive")
        by_cell: dict[tuple[str, str, int, int, int, str], SparseActivation] = {}
        for activation in self.activations:
            key = activation.cell.stable_key()
            current = by_cell.get(key)
            if current is None or _activation_sort_key(activation) < _activation_sort_key(current):
                by_cell[key] = activation
        ordered = tuple(sorted(by_cell.values(), key=_activation_sort_key)[:beam])
        return ActivationFrontier(self.step, ordered)


def propagate_score(score_q16: int, weight_q16: int) -> int:
    return q16_mul(score_q16, weight_q16)


def _activation_sort_key(activation: SparseActivation) -> tuple[int, tuple[str, str, int, int, int, str], str]:
    return (-activation.score_q16, activation.cell.stable_key(), activation.path_id)
