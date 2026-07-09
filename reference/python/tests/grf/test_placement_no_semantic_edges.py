from __future__ import annotations

import json

from test_placement_candidate import candidate
from test_minimal_admission_record import placement


def test_placement_objects_do_not_contain_forbidden_relation_terms() -> None:
    payloads = [candidate().to_mapping(), placement().to_mapping()]
    text = json.dumps(payloads, sort_keys=True)
    for forbidden in ("semantic_edge", "parent", "topic"):
        assert forbidden not in text
