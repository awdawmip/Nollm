from __future__ import annotations

import unittest

from nollm.chart_gluing import LocalChartSpec
from nollm.dream_placement import (
    DreamPlacementCandidate,
    PlacementEnergy,
    candidate_addresses_for_chart,
    placement_candidate_from_record,
    placement_candidate_to_record,
    rank_placement_candidates,
)
from nollm.geometry import HexAddress


class DreamPlacementTests(unittest.TestCase):
    def chart(self) -> LocalChartSpec:
        return LocalChartSpec(
            chart_id="chart-a",
            seed=HexAddress(2, 3, -1),
            source_radius=1,
            layer_ids=(2,),
            parameter_signature="params",
        )

    def candidate(
        self,
        shard_id: str = "shard-a",
        chart_id: str = "chart-a",
        address: HexAddress | None = None,
        energy: PlacementEnergy | None = None,
    ) -> DreamPlacementCandidate:
        return DreamPlacementCandidate(
            shard_id=shard_id,
            chart_id=chart_id,
            address=address or HexAddress(0, 0, 0),
            energy=energy or PlacementEnergy(),
            anchors_used=("geometry",),
            reasons=("explicit hint",),
        )

    def test_placement_energy_total_sums_all_terms(self) -> None:
        energy = PlacementEnergy(
            semantic_hint_cost=1.0,
            geometric_distance_cost=2.0,
            density_pressure_cost=3.0,
            coverage_potential_cost=4.0,
            future_scan_cost=5.0,
            merge_complexity_cost=6.0,
            compute_cost=7.0,
        )
        self.assertAlmostEqual(energy.total, 28.0)

    def test_negative_energy_terms_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            PlacementEnergy(semantic_hint_cost=-0.1)
        with self.assertRaises(ValueError):
            PlacementEnergy(compute_cost=True)  # type: ignore[arg-type]

    def test_candidate_validates_status_and_address_type(self) -> None:
        candidate = self.candidate(shard_id="shard-a")
        self.assertEqual(candidate.shard_id, "shard-a")
        with self.assertRaises(ValueError):
            DreamPlacementCandidate(
                shard_id="bad",
                chart_id="chart-a",
                address="not-address",  # type: ignore[arg-type]
                energy=PlacementEnergy(),
            )

    def test_unknown_placement_status_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            DreamPlacementCandidate(
                shard_id="bad",
                chart_id="chart-a",
                address=HexAddress(0, 0, 0),
                energy=PlacementEnergy(),
                status="confirmed",
            )

    def test_anchor_hints_and_reasons_must_be_non_empty_strings(self) -> None:
        invalids = [
            {"anchors_used": ("",)},
            {"anchors_used": (1,)},
            {"reasons": ("",)},
            {"reasons": (1,)},
        ]
        for override in invalids:
            with self.subTest(override=override):
                params = {
                    "shard_id": "bad",
                    "chart_id": "chart-a",
                    "address": HexAddress(0, 0, 0),
                    "energy": PlacementEnergy(),
                }
                params.update(override)
                with self.assertRaises(ValueError):
                    DreamPlacementCandidate(**params)  # type: ignore[arg-type]

    def test_rank_placement_candidates_is_deterministic(self) -> None:
        high = self.candidate(
            shard_id="shard-c",
            address=HexAddress(0, 0, 0),
            energy=PlacementEnergy(compute_cost=3.0),
        )
        tie_b = self.candidate(
            shard_id="shard-b",
            address=HexAddress(0, 0, 1),
            energy=PlacementEnergy(compute_cost=1.0),
        )
        tie_a = self.candidate(
            shard_id="shard-a",
            address=HexAddress(0, 0, 0),
            energy=PlacementEnergy(compute_cost=1.0),
        )
        self.assertEqual(
            [item.shard_id for item in rank_placement_candidates([high, tie_b, tie_a])],
            ["shard-a", "shard-b", "shard-c"],
        )

    def test_record_roundtrip(self) -> None:
        candidate = DreamPlacementCandidate(
            shard_id="shard-a",
            chart_id="chart-a",
            address=HexAddress(1, 2, -3),
            energy=PlacementEnergy(semantic_hint_cost=0.5, compute_cost=1.5),
            anchors_used=("anchor-a",),
            reasons=("explicit numeric hint",),
            status="placed_uncertain",
        )
        self.assertEqual(placement_candidate_from_record(placement_candidate_to_record(candidate)), candidate)

    def test_candidate_addresses_for_chart_returns_deterministic_disk(self) -> None:
        addresses = candidate_addresses_for_chart(self.chart())
        self.assertEqual(len(addresses), 7)
        self.assertEqual(addresses[0], HexAddress(2, 2, -1))
        self.assertEqual(addresses, sorted(addresses, key=lambda item: (item.layer, item.q, item.r)))

    def test_candidate_generation_has_no_ownership_semantics(self) -> None:
        candidate = self.candidate()
        for forbidden_attr in ("parent", "child", "children", "owner", "belongs_to"):
            self.assertFalse(hasattr(candidate, forbidden_attr))
        statuses = {"candidate", "placed_uncertain", "new_chart_candidate", "rejected"}
        for forbidden_word in ("confirmed", "parent", "owner"):
            self.assertTrue(all(forbidden_word not in status for status in statuses))


if __name__ == "__main__":
    unittest.main()
