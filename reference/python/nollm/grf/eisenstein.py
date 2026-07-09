"""Eisenstein integer helper for exact axial transforms."""

from __future__ import annotations

from dataclasses import dataclass

from .axial import AxialCoord


@dataclass(frozen=True, order=True)
class EisensteinInt:
    a: int
    b: int

    def __post_init__(self) -> None:
        if type(self.a) is not int or type(self.b) is not int:
            raise TypeError("Eisenstein coefficients must be integers")

    @property
    def norm(self) -> int:
        return self.a * self.a + self.a * self.b + self.b * self.b

    @property
    def matrix(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return ((self.a, -self.b), (self.b, self.a + self.b))

    def apply_to_axial(self, coord: AxialCoord) -> AxialCoord:
        matrix = self.matrix
        return AxialCoord(
            matrix[0][0] * coord.q + matrix[0][1] * coord.r,
            matrix[1][0] * coord.q + matrix[1][1] * coord.r,
        )

    def compose(self, other: "EisensteinInt") -> "EisensteinInt":
        return EisensteinInt(self.a * other.a - self.b * other.b, self.a * other.b + self.b * other.a + self.b * other.b)

    @staticmethod
    def identity() -> "EisensteinInt":
        return EisensteinInt(1, 0)
