from __future__ import annotations

from nollm.grf.fixed_point import Q16_ONE, WEIGHT_FORMAT, normalize_q16_weights, q16_from_ratio, q16_mul, q16_sum, residual_q16


def test_q16_denominator_is_65536() -> None:
    assert Q16_ONE == 65536
    assert WEIGHT_FORMAT == "q16_65536"
    assert q16_from_ratio(1, 2) == 32768


def test_q16_math_uses_integer_residuals() -> None:
    weights = normalize_q16_weights([1, 1, 1])
    assert q16_sum(weights) == Q16_ONE
    assert residual_q16(weights) == 0
    assert q16_mul(Q16_ONE, weights[0]) == weights[0]
    assert weights == (21846, 21845, 21845)
