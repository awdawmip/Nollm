from __future__ import annotations

import unittest

from nollm.cluster_pressure import (
    coarse_emergence_to_record,
    pressure_sample_to_record,
    propose_coarse_emergence,
    summarize_pressure,
)
from nollm.dream_placement import (
    DreamPlacementCandidate,
    PlacementEnergy,
    placement_candidate_to_record,
    rank_placement_candidates,
)
from nollm.dream_shard import DreamShard, shard_to_record
from nollm.geometry import HexAddress
from nollm.parameter_experiments import (
    default_parameter_regimes,
    evaluate_parameter_regime,
    parameter_result_to_record,
    rank_parameter_results,
)
from nollm.scale_scan_traversal import (
    make_linear_scale_scan_plan,
    scale_scan_plan_to_record,
)


FORBIDDEN_FIELDS = {"parent_id", "children", "owner_anchor", "belongs_to_anchor"}


class DreamGeometryPipelineTests(unittest.TestCase):
    def test_d_series_records_form_deterministic_candidate_pipeline(self) -> None:
        shard = DreamShard(
            shard_id="pipeline-shard",
            text="Pipeline shards remain explicit candidate material.",
            anchors_hint=("pipeline",),
        )

        placements = [
            DreamPlacementCandidate(
                shard_id=shard.shard_id,
                chart_id="pipeline-chart",
                address=HexAddress(0, 0, 0),
                energy=PlacementEnergy(compute_cost=1.0),
                reasons=("pipeline candidate",),
            ),
            DreamPlacementCandidate(
                shard_id=shard.shard_id,
                chart_id="pipeline-chart",
                address=HexAddress(0, 1, -1),
                energy=PlacementEnergy(compute_cost=0.5),
                reasons=("lower energy candidate",),
            ),
        ]
        ranked_placements = rank_placement_candidates(reversed(placements))

        pressure_samples = summarize_pressure(ranked_placements, "pipeline-chart")
        coarse = propose_coarse_emergence(
            pressure_samples,
            "pipeline-chart",
            HexAddress(0, 0, 0),
            radius=1,
        )
        plan = make_linear_scale_scan_plan(
            shard.shard_id,
            "pipeline-chart",
            ranked_placements[0].address,
            max_layers=1,
            radius=1,
        )
        parameter_results = rank_parameter_results(
            evaluate_parameter_regime(regime, 8)
            for regime in default_parameter_regimes()
        )

        records = [
            shard_to_record(shard),
            *[placement_candidate_to_record(item) for item in ranked_placements],
            *[pressure_sample_to_record(item) for item in pressure_samples],
            coarse_emergence_to_record(coarse),
            scale_scan_plan_to_record(plan),
            parameter_result_to_record(parameter_results[0]),
        ]

        self.assertEqual(shard.shard_id, "pipeline-shard")
        self.assertEqual(ranked_placements[0].status, "candidate")
        self.assertEqual(coarse.status, "candidate")
        self.assertEqual(plan.status, "candidate")
        self.assertNotEqual(ranked_placements[0].status, "confirmed")
        self.assertTrue(all(_is_primitive_serializable(record) for record in records))
        self.assertTrue(all(not _has_forbidden_field(record) for record in records))
        self.assertEqual(
            [item.address.q for item in ranked_placements],
            [1, 0],
        )


def _is_primitive_serializable(value: object) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_primitive_serializable(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_primitive_serializable(item) for key, item in value.items())
    return False


def _has_forbidden_field(value: object) -> bool:
    if isinstance(value, dict):
        return any(key in FORBIDDEN_FIELDS or _has_forbidden_field(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_forbidden_field(item) for item in value)
    return False


if __name__ == "__main__":
    unittest.main()
