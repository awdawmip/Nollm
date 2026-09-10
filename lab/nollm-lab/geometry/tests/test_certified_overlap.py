"""Independent arithmetic/golden checks. Lab imports must never enter Core."""
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from certified_overlap import (  # noqa: E402
    CertificationBudgetExceeded, DyadicInterval as I, HEX, NORMALS,
    area, certify_coverage, clip_halfplane, coverage_enclosure, ideal_transform,
)


def test_interval_operations_enclose_rational_endpoints():
    s = 1 << 64
    for aa in ((-3*s, -s//3), (0, s), (s//3, 3*s)):
        for bb in ((-5*s, -s//7), (s//5, 2*s)):
            a, b = I(*aa, 64), I(*bb, 64)
            for op in (lambda x,y:x+y, lambda x,y:x-y, lambda x,y:x*y, lambda x,y:x/y):
                out = op(a,b)
                for x in (a.lower, a.upper):
                    for y in (b.lower, b.upper):
                        assert out.lower <= op(x,y) <= out.upper
    for n in (0, 1, 2, 3, 4, 999):
        value = I.integer(n,64).sqrt()
        assert value.lower**2 <= n <= value.upper**2
    with pytest.raises(ZeroDivisionError):
        I(-1,1,64).reciprocal()
    with pytest.raises(ValueError):
        I(-2,-1,64).sqrt()


def test_halfplanes_and_boundary_only_clips():
    assert area(HEX) == 1
    for a,b in NORMALS:
        assert area(clip_halfplane(HEX,F(a),F(b),F(1))) == 1
        assert area(clip_halfplane(HEX,F(a),F(b),F(0))) == F(1,2)
        assert area(clip_halfplane(HEX,F(a),F(b),F(-1))) == 0
        assert area(clip_halfplane(HEX,F(a),F(b),F(-2))) == 0


def _matmul(a,b):
    return tuple(sum((a[2*i+k]*b[2*k+j] for k in range(2)), I.integer(0,a[0].bits))
                 for i in range(2) for j in range(2))


def test_ideal_transform_inverse_and_eight_layer_enclosures():
    down, up = ideal_transform('coverage_down',128), ideal_transform('coverage_up',128)
    for x,n in zip(_matmul(down,up),(1,0,0,1)):
        assert x.lower <= n <= x.upper
        assert x.upper-x.lower < F(1,1<<110)
    power = down
    for _ in range(7):
        power = _matmul(power,down)
    for x,n in zip(power,(-4,0,0,-4)):
        assert x.lower <= n <= x.upper
        assert x.upper-x.lower < F(1,1<<100)
    # Independent frozen nearest-Q40 coefficient witness, not the truth source.
    for direction, expected in (
        ('coverage_up',(649918386859,-408555777664,408555777664,1058474164523)),
        ('coverage_down',(1496908518890,577785121758,-577785121758,919123397132)),
    ):
        for x,n in zip(ideal_transform(direction,128),expected):
            assert round(x.lower*(1<<40)) == round(x.upper*(1<<40)) == n


def test_origin_has_analytic_area_golden_values():
    up = certify_coverage(0,0,0,'coverage_up')
    assert up.shares() == {(0,0):(F(1),F(1))}
    down = certify_coverage(0,0,0,'coverage_down')
    assert len(down.members) == 7
    lo,hi = down.shares()[(0,0)]
    assert lo*lo <= F(1,2) <= hi*hi
    for m in down.members:
        if (m.q,m.r) != (0,0):
            assert max(m.lower,(1-hi)/6) <= min(m.upper,(1-lo)/6)
    assert down.total_lower <= 1 <= down.total_upper
    assert down.total_width <= F(1,1<<64)


@pytest.mark.parametrize('direction',('coverage_up','coverage_down'))
def test_large_negative_coordinates_and_layer_covariance(direction):
    for q,r in ((19,-17),(10**9,-10**9),(-10**9,0),(0,(1<<31)-1)):
        result = certify_coverage(0,q,r,direction)
        opposite = certify_coverage(0,-q,-r,direction)
        assert result.total_width <= F(1,1<<64)
        assert result.total_lower <= 1 <= result.total_upper
        assert result.candidate_count <= 64
        assert all(0 < m.upper <= 1 for m in result.members)
        mirror = {(-m.q,-m.r):(m.lower,m.upper) for m in opposite.members}
        for key,(lo,hi) in result.shares().items():
            a,b = mirror.get(key,(F(0),F(0)))
            assert max(lo,a) <= min(hi,b)
        for layer in (-63,7,63):
            assert certify_coverage(layer,q,r,direction).shares() == result.shares()


def test_reciprocal_source_share_area_law():
    forward = certify_coverage(0,7,-3,'coverage_down')
    sqrt2 = I.integer(2,192).sqrt()
    for m in forward.members:
        back = certify_coverage(1,m.q,m.r,'coverage_up').shares()
        a,b = back.get((7,-3),(F(0),F(0)))
        assert max(a,m.lower*sqrt2.lower) <= min(b,m.upper*sqrt2.upper)


def test_exact_error_observer_detects_missing_mass():
    result = certify_coverage(0,0,0,'coverage_down')
    comparison = result.compare_q16({(0,0):65536})
    for lo,hi in comparison.values():
        # Exact answer 1-1/sqrt(2), tested without an approximate sqrt.
        assert (1-hi)**2 <= F(1,2) <= (1-lo)**2
    exact = certify_coverage(0,0,0,'coverage_up')
    assert exact.compare_q16({(0,0):65536})['total_variation'] == (0,0)
    assert exact.compare_q16({(99,99):65536})['total_variation'] == (1,1)
    assert exact.compare_q16({(99,99):65536})['missed_mass'] == (1,1)
    with pytest.raises(ValueError):
        result.compare_q16({(0,0):65535})
    with pytest.raises(TypeError):
        result.compare_q16({('zero',0):65536})


@pytest.mark.parametrize('args',(
    (True,0,0,'coverage_up'), (0,0.0,0,'coverage_down'),
    (0,0,False,'coverage_up'), (65,0,0,'coverage_up'),
    (-64,0,0,'coverage_up'), (64,0,0,'coverage_down'),
    (0,1<<31,0,'coverage_down'), (0,0,0,'lateral'),
))
def test_invalid_geometry_fails_explicitly(args):
    with pytest.raises((TypeError,ValueError)):
        coverage_enclosure(*args)


def test_precision_candidate_budgets_and_cached_type_validation():
    with pytest.raises(CertificationBudgetExceeded):
        coverage_enclosure(0,0,0,'coverage_down',max_candidates=1)
    with pytest.raises(CertificationBudgetExceeded):
        certify_coverage(0,123,-79,'coverage_down',tolerance=F(1,1<<200),max_bits=64)
    with pytest.raises(ValueError):
        certify_coverage(0,0,0,'coverage_down',tolerance=0.1)
    ideal_transform('coverage_down',64)
    with pytest.raises(TypeError):
        ideal_transform('coverage_down',64.0)
    with pytest.raises(TypeError):
        ideal_transform('coverage_down',True)
