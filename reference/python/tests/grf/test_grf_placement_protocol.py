from __future__ import annotations

import pytest

from nollm.grf.cell_address import CellAddress
from nollm.grf.placement_protocol import NollmPlacementDecision, NollmPlacementRequest, validate_decision


def _request() -> NollmPlacementRequest:
    return NollmPlacementRequest("request:one", "shard:one", (CellAddress("eisenstein_exact_v1", "chart:one", 0, 1, -1),), candidate_reuse_placements=("placement:old",), stitch_candidates=("stitch:one",))


def test_explicit_new_decision_is_accepted_without_semantic_scoring() -> None:
    request = _request()
    decision = NollmPlacementDecision("decision:one", request.request_id, "new", "bounded model decision", request.candidate_cells[0], "candidate:one", "placement:one")
    validate_decision(request, decision)


def test_decision_cannot_escape_explicit_candidates() -> None:
    request = _request()
    decision = NollmPlacementDecision("decision:two", request.request_id, "revision", "bounded model decision", CellAddress("eisenstein_exact_v1", "chart:one", 0, 2, -1), "candidate:two", "placement:two")
    with pytest.raises(ValueError, match="outside"):
        validate_decision(request, decision)


def test_defer_is_normal_and_carries_no_mutation() -> None:
    request = _request()
    validate_decision(request, NollmPlacementDecision("decision:defer", request.request_id, "defer", "uncertain"))
