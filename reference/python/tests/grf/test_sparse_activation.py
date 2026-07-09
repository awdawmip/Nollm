from __future__ import annotations

from nollm.grf.cell_address import CellAddress
from nollm.grf.fixed_point import Q16_ONE
from nollm.grf.propagation import ActivationFrontier, SparseActivation, propagate_score


def test_activation_frontier_merges_and_prunes_deterministically() -> None:
    a = CellAddress("eisenstein_exact_v1", "chart_a", 0, 0, 0)
    b = CellAddress("eisenstein_exact_v1", "chart_a", 0, 1, 0)
    frontier = ActivationFrontier(1, (SparseActivation(b, Q16_ONE // 2, "p2"), SparseActivation(a, Q16_ONE, "p1"), SparseActivation(a, Q16_ONE // 4, "p3")))
    merged = frontier.merged(1)
    assert merged.activations == (SparseActivation(a, Q16_ONE, "p1"),)


def test_propagate_score_uses_q16_integer() -> None:
    assert propagate_score(Q16_ONE // 2, Q16_ONE // 2) == Q16_ONE // 4
