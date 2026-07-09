"""Q16 fixed-point weights for GRF coverage templates."""

from __future__ import annotations

Q16_ONE = 65536
WEIGHT_FORMAT = "q16_65536"


def q16_from_ratio(numer: int, denom: int) -> int:
    if type(numer) is not int or type(denom) is not int:
        raise TypeError("ratio terms must be integers")
    if denom <= 0:
        raise ValueError("denominator must be positive")
    return (numer * Q16_ONE + denom // 2) // denom


def q16_mul(left: int, right: int) -> int:
    _require_q16(left)
    _require_q16(right)
    return (left * right + Q16_ONE // 2) // Q16_ONE


def q16_sum(values: tuple[int, ...] | list[int]) -> int:
    for value in values:
        _require_q16(value)
    return sum(values)


def normalize_q16_weights(raw_weights: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    if not raw_weights:
        raise ValueError("weights cannot be empty")
    for value in raw_weights:
        if type(value) is not int or value < 0:
            raise ValueError("weights must be non-negative integers")
    total = sum(raw_weights)
    if total <= 0:
        raise ValueError("weight total must be positive")
    provisional = [(value * Q16_ONE) // total for value in raw_weights]
    remainder = Q16_ONE - sum(provisional)
    order = sorted(range(len(raw_weights)), key=lambda idx: (-((raw_weights[idx] * Q16_ONE) % total), idx))
    for idx in order[:remainder]:
        provisional[idx] += 1
    return tuple(provisional)


def residual_q16(weights: tuple[int, ...] | list[int]) -> int:
    return Q16_ONE - q16_sum(weights)


def _require_q16(value: int) -> None:
    if type(value) is not int:
        raise TypeError("Q16 value must be an integer")
