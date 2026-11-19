import unittest

from directional_probe import run


class DirectionalCoverageTest(unittest.TestCase):
    def test_both_directional_disagreements_and_surface_witness(self):
        result = run(certify=True)
        self.assertEqual([row["sampled_q16"] for row in result["up_only"]], [0, 683])
        self.assertEqual([row["sampled_q16"] for row in result["down_only"]], [683, 0])
        for row in result["up_only"] + result["down_only"]:
            self.assertGreater(row["ideal_source_share_ppm_bounds"][0], 0)
        witness = result["reopened_surface_witness"]
        self.assertEqual(witness["surface_membership_q16"], 683)
        self.assertEqual(witness["surface_tile_count"], 4)
        self.assertEqual(witness["surface_total_mass_q16"], 65536)
        self.assertEqual(witness["physical_recall_items"], 0)
        self.assertTrue(witness["state_bytes_unchanged_after_reopen_and_queries"])
