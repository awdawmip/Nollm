from __future__ import annotations

import inspect

import pytest

from nollm.grf.axial import AxialCoord, CubeCoord, axial_to_cube, cube_to_axial, hex_distance, hex_neighbors, hex_ring
import nollm.grf.axial as axial


def test_axial_cube_roundtrip_and_distance_are_integer() -> None:
    coord = AxialCoord(2, -5)
    cube = axial_to_cube(coord)
    assert cube == CubeCoord(2, -5, 3)
    assert cube_to_axial(cube) == coord
    assert hex_distance(AxialCoord(2, -1), AxialCoord(-1, 3)) == 4


def test_cube_invariant_and_float_rejection() -> None:
    with pytest.raises(ValueError):
        CubeCoord(1, 2, 3)
    with pytest.raises(TypeError):
        AxialCoord(1.0, 0)  # type: ignore[arg-type]


def test_neighbors_and_ring_are_deterministic() -> None:
    center = AxialCoord(0, 0)
    assert len(hex_neighbors(center)) == 6
    ring = hex_ring(center, 2)
    assert len(ring) == 12
    assert ring == tuple(sorted(ring, key=lambda item: (item.q, item.r)))
    assert all(hex_distance(cell, center) == 2 for cell in ring)


def test_axial_runtime_source_has_no_float() -> None:
    assert "float" not in inspect.getsource(axial)
