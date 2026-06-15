from __future__ import annotations

import unittest

from nollm.parameter_experiments import (
    ParameterRegime,
    default_parameter_regimes,
    evaluate_parameter_regime,
    parameter_regime_from_record,
    parameter_regime_to_record,
    parameter_result_from_record,
    parameter_result_to_record,
    rank_parameter_results,
)


class ParameterExperimentTests(unittest.TestCase):
    def test_default_regimes_are_present(self) -> None:
        descriptions = {regime.description for regime in default_parameter_regimes()}
        self.assertIn("2^(1/4) + 15 deg", descriptions)
        self.assertIn("2^(1/4) + 22.5 deg", descriptions)
        self.assertIn("sqrt(2) + 15 deg", descriptions)
        self.assertIn("phi + 15 deg", descriptions)
        self.assertIn("sqrt(3) + 30 deg benchmark", descriptions)

    def test_invalid_beta_theta_layers_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ParameterRegime("bad", 0.0, 15.0, "bad")
        with self.assertRaises(ValueError):
            ParameterRegime("bad", 1.0, -1.0, "bad")
        with self.assertRaises(ValueError):
            evaluate_parameter_regime(ParameterRegime("ok", 1.2, 15.0, "ok"), -1)

    def test_record_round_trips(self) -> None:
        regime = ParameterRegime("r", 2 ** 0.25, 22.5, "regime")
        result = evaluate_parameter_regime(regime, 8)
        self.assertEqual(parameter_regime_from_record(parameter_regime_to_record(regime)), regime)
        self.assertEqual(parameter_result_from_record(parameter_result_to_record(result)), result)

    def test_ranking_is_deterministic(self) -> None:
        regimes = default_parameter_regimes()
        results = [evaluate_parameter_regime(regime, 8) for regime in reversed(regimes)]
        ranked_once = rank_parameter_results(results)
        ranked_twice = rank_parameter_results(reversed(results))
        self.assertEqual(
            [item.regime_id for item in ranked_once],
            [item.regime_id for item in ranked_twice],
        )

    def test_22_5_regime_hits_zero_mod_60_after_eight_layers(self) -> None:
        regime = [item for item in default_parameter_regimes() if item.regime_id == "beta_2q_22_5"][0]
        result = evaluate_parameter_regime(regime, 8)
        self.assertTrue(result.rotation_cycle_hit)


if __name__ == "__main__":
    unittest.main()
