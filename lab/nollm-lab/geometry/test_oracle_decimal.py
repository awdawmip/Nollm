from decimal import Decimal

from oracle_decimal import coverage, fractional_target_axial


def test_fractional_target_address_depends_on_complete_source_address() -> None:
    origin = fractional_target_axial(0, 0, 0, 1)
    translated = fractional_target_axial(0, 3, -2, 1)
    assert origin == (Decimal(0), Decimal(0))
    assert translated != origin


def test_coverage_support_is_translation_covariant_not_phase_constant() -> None:
    origin = {(item.q, item.r) for item in coverage(0, 0, 0, 1)}
    translated = {(item.q, item.r) for item in coverage(0, -4, 1, 1)}
    assert 4 <= len(origin) <= 7
    assert 4 <= len(translated) <= 7
    assert origin != translated
    assert sum(item.source_share for item in coverage(0, -4, 1, 1)) <= Decimal(1) + Decimal("1e-26")
