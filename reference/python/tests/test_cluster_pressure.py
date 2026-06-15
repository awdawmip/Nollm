from __future__ import annotations

import unittest

from nollm.cluster_pressure import (
    ClusterPressureSample,
    CoarseEmergenceCandidate,
    coarse_emergence_from_record,
    coarse_emergence_to_record,
    pressure_sample_from_record,
    pressure_sample_to_record,
    propose_coarse_emergence,
    rank_pressure_samples,
    summarize_pressure,
)
from nollm.dream_placement import DreamPlacementCandidate, PlacementEnergy
from nollm.geometry import HexAddress


class ClusterPressureTests(unittest.TestCase):
    def placement(self, address: HexAddress, cost: float = 0.0) -> DreamPlacementCandidate:
        return DreamPlacementCandidate(
            shard_id=f"shard-{address.q}-{address.r}-{cost}",
            chart_id="chart-a",
            address=address,
            energy=PlacementEnergy(compute_cost=cost),
            reasons=("candidate pressure",),
        )

    def test_validation_rejects_negative_values(self) -> None:
        with self.assertRaises(ValueError):
            ClusterPressureSample("chart-a", HexAddress(0, 0, 0), -1, 0.0)
        with self.assertRaises(ValueError):
            ClusterPressureSample("chart-a", HexAddress(0, 0, 0), 1, -0.1)
        with self.assertRaises(ValueError):
            CoarseEmergenceCandidate("chart-a", HexAddress(0, 0, 0), -1, 0.0, 0)

    def test_records_round_trip(self) -> None:
        sample = ClusterPressureSample("chart-a", HexAddress(0, 1, -1), 2, 1.5, ("reason",))
        coarse = CoarseEmergenceCandidate("chart-a", HexAddress(0, 0, 0), 2, 3.0, 1)
        self.assertEqual(pressure_sample_from_record(pressure_sample_to_record(sample)), sample)
        self.assertEqual(coarse_emergence_from_record(coarse_emergence_to_record(coarse)), coarse)

    def test_ranking_is_deterministic(self) -> None:
        samples = [
            ClusterPressureSample("chart-a", HexAddress(0, 1, 0), 1, 1.0),
            ClusterPressureSample("chart-a", HexAddress(0, 0, 0), 2, 1.0),
            ClusterPressureSample("chart-a", HexAddress(0, 2, 0), 1, 2.0),
        ]
        ranked = rank_pressure_samples(samples)
        self.assertEqual([item.address.q for item in ranked], [2, 0, 1])

    def test_summarize_and_coarse_emergence_are_candidate_only(self) -> None:
        placements = [
            self.placement(HexAddress(0, 0, 0)),
            self.placement(HexAddress(0, 0, 0), cost=1.0),
            self.placement(HexAddress(0, 1, 0)),
        ]
        samples = summarize_pressure(placements, chart_id="chart-a")
        self.assertEqual(samples[0].placement_count, 2)
        coarse = propose_coarse_emergence(samples, "chart-a", HexAddress(0, 0, 0), radius=1)
        self.assertEqual(coarse.status, "candidate")
        self.assertEqual(coarse.sample_count, 2)

    def test_no_parent_children_fields(self) -> None:
        sample = ClusterPressureSample("chart-a", HexAddress(0, 0, 0), 1, 1.0)
        coarse = CoarseEmergenceCandidate("chart-a", HexAddress(0, 0, 0), 0, 1.0, 1)
        for obj in (sample, coarse):
            for name in ("parent", "children", "owner", "belongs_to"):
                self.assertFalse(hasattr(obj, name))


if __name__ == "__main__":
    unittest.main()
