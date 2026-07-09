from __future__ import annotations

import inspect

from nollm.grf.axial import AxialCoord
from nollm.grf.eisenstein import EisensteinInt
import nollm.grf.eisenstein as eisenstein


def _matmul(left: tuple[tuple[int, int], tuple[int, int]], right: tuple[tuple[int, int], tuple[int, int]]) -> tuple[tuple[int, int], tuple[int, int]]:
    return (
        (left[0][0] * right[0][0] + left[0][1] * right[1][0], left[0][0] * right[0][1] + left[0][1] * right[1][1]),
        (left[1][0] * right[0][0] + left[1][1] * right[1][0], left[1][0] * right[0][1] + left[1][1] * right[1][1]),
    )


def test_norm_is_multiplicative() -> None:
    first = EisensteinInt(2, 1)
    second = EisensteinInt(1, 3)
    assert first.compose(second).norm == first.norm * second.norm


def test_matrix_composition_matches_eisenstein_multiplication() -> None:
    first = EisensteinInt(2, -1)
    second = EisensteinInt(3, 2)
    assert first.compose(second).matrix == _matmul(first.matrix, second.matrix)


def test_apply_to_axial_is_exact_and_deterministic() -> None:
    transform = EisensteinInt(2, 1)
    coord = AxialCoord(4, -3)
    assert transform.apply_to_axial(coord) == transform.apply_to_axial(coord)
    assert EisensteinInt.identity().apply_to_axial(coord) == coord


def test_eisenstein_source_has_no_float() -> None:
    assert "float" not in inspect.getsource(eisenstein)
