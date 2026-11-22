"""Independent exact scalar oracle and adversarial inputs for adaptive Lab maps.

This test covers point enclosures and labels of explicit rational Lab maps. It deliberately does
not call RationalAffine.forward/inverse or RationalRadialTwist._map. All values
are Fractions; the tests compare point containment, not approximate equality.
"""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction as F
from math import lcm
import unittest

from geometry.rational_geometry import RationalAffine, RationalLayerMap, RationalRadialTwist
from geometry.adaptive_rational_kernel import compile_adaptive_pair, certify_target_box


def exact_affine(frame, point, inverse=False):
    (a, b), (c, d) = frame.matrix
    q, r = map(F, point)
    if inverse:
        q, r = q-frame.origin[0], r-frame.origin[1]
        determinant = a*d-b*c
        return ((d*q-b*r)/determinant+frame.local_anchor[0],
                (a*r-c*q)/determinant+frame.local_anchor[1])
    q, r = q-frame.local_anchor[0], r-frame.local_anchor[1]
    return a*q+b*r+frame.origin[0], c*q+d*r+frame.origin[1]


def exact_twist(twist, point, inverse=False):
    q, r = map(F, point)
    u, v = q-twist.center[0], r-twist.center[1]
    radius = u*u+u*v+v*v
    if radius >= twist.radius_squared or twist.strength == 0:
        return q, r
    t = twist.strength*(twist.radius_squared-radius)**2/twist.radius_squared**2
    if inverse:
        t = -t
    divisor = 1+3*t*t
    return (twist.center[0]+((1-3*t*t-2*t)*u-4*t*v)/divisor,
            twist.center[1]+(4*t*u+(1-3*t*t+2*t)*v)/divisor)


def exact_relative(source, target, point):
    point = exact_affine(source.frame, point)
    for twist in source.twists:
        point = exact_twist(twist, point)
    for twist in reversed(target.twists):
        point = exact_twist(twist, point, inverse=True)
    return exact_affine(target.frame, point, inverse=True)


def independent_nearest_candidates(point):
    """Minimize axial distance directly, independently of cube rounding.

    All nearest centers lie within one in both coordinates of their floors.
    A strict certificate has one minimizer. Ties are tested separately using
    the existing specified half-even / cube-repair order.
    """
    q, r = point
    aq, ar = q.numerator//q.denominator, r.numerator//r.denominator
    scores = {}
    for cq in range(aq-1, aq+3):
        for cr in range(ar-1, ar+3):
            u, v = q-cq, r-cr
            scores[cq, cr] = u*u+u*v+v*v
    minimum = min(scores.values())
    return {cell for cell, value in scores.items() if value == minimum}


def joint_ratio(point):
    q, r = map(F, point)
    divisor = lcm(q.denominator, r.denominator)
    return q.numerator*(divisor//q.denominator), r.numerator*(divisor//r.denominator), divisor


def cases():
    identity = RationalLayerMap()
    first = RationalRadialTwist((F(1,7), F(-2,11)), F(25,3), F(2,5))
    second = RationalRadialTwist((F(-3,10), F(1,4)), F(7,2), F(-1,3))
    frame = RationalAffine(((F(7,6), F(-1,7)), (F(2,9), F(13,12))),
                           (F(1,17), F(-3,19)), (F(2,11), F(-1,13)))
    target = RationalAffine(((F(3,2), F(1,5)), (F(-1,11), F(4,5))),
                            (F(1,3), F(2,7)), (F(-2,9), F(1,5)))
    yield ('distinct_twists', RationalLayerMap(frame, (first,)),
           RationalLayerMap(target, (second,)), (F(1,7), F(-2,9)))
    yield ('two_centers', RationalLayerMap(frame, (first, second)), identity,
           (F(-1,5), F(2,7)))
    # The very large integer world component cancels exactly before execution.
    anchor = 2**180+1
    shifted_first = replace(first, center=(anchor+first.center[0], -anchor+first.center[1]))
    shifted_second = replace(second, center=(anchor+second.center[0], -anchor+second.center[1]))
    yield ('large_world_anchor',
           RationalLayerMap(replace(frame, origin=(anchor+F(1,17),-anchor-F(3,19))), (shifted_first,)),
           RationalLayerMap(replace(target, origin=(anchor+F(1,3),-anchor+F(2,7))), (shifted_second,)),
           (F(1,7), F(-2,9)))
    # A tiny positive radius² must not acquire an artificial division by zero.
    tiny = RationalRadialTwist((0,0), F(1,2**120), F(1,3))
    yield ('tiny_radius', RationalLayerMap(twists=(tiny,)), identity,
           (F(1,2**61), F(1,2**64)))
    near_singular = RationalAffine(((1,1),(1,1+F(1,2**45))))
    yield ('ill_conditioned_inverse', RationalLayerMap(twists=(first,)),
           RationalLayerMap(near_singular), (F(1,3), F(-1,4)))
    huge_strength = RationalRadialTwist((0,0), 1, 2**20)
    yield ('large_strength', RationalLayerMap(twists=(huge_strength,)), identity,
           (F(1,3), F(-1,5)))
    edge = RationalRadialTwist((0,0),1,F(5,7))
    for delta in (-F(1,2**70),0,F(1,2**70)):
        yield ('cutoff_'+str(delta), RationalLayerMap(twists=(edge,)), identity, (1+delta,0))
    common = RationalRadialTwist((F(1,3),F(-2,5)),4,F(1,7))
    yield ('common_outer_suffix', RationalLayerMap(twists=(first,common)),
           RationalLayerMap(twists=(second,common)), (F(1,5),F(1,7)))
    yield ('inverse_chain_order', RationalLayerMap(), RationalLayerMap(twists=(first,second)),
           (F(-1,5),F(1,11)))
    yield ('outside_support', RationalLayerMap(twists=(first,second)), identity, (17,-23))
    # A distinct, disjoint twist forces the nonlinear evaluator while leaving
    # the exact point unchanged. This isolates the boundary/tie predicate.
    disjoint = RationalRadialTwist((1000,1000),1,F(1,3))
    for q in (F(1,2),F(3,2),F(-1,2),F(-3,2)):
        yield ('tie_q_'+str(q),RationalLayerMap(twists=(disjoint,)),identity,(q,0))
    yield ('non_dyadic_vertex_tie',RationalLayerMap(twists=(disjoint,)),identity,(F(1,3),F(1,3)))
    for delta in (-F(1,2**300),F(1,2**300)):
        yield ('beyond_max_bits_'+str(delta),RationalLayerMap(twists=(disjoint,)),identity,(F(1,2)+delta,0))


TIE_TARGETS = {
    'tie_q_1/2': (0,0),
    'tie_q_3/2': (2,0),
    'tie_q_-1/2': (0,0),
    'tie_q_-3/2': (-2,0),
    'non_dyadic_vertex_tie': (1,0),
}


def expected_cell(name, point):
    nearest = independent_nearest_candidates(point)
    if name in TIE_TARGETS:
        expected = TIE_TARGETS[name]
        assert expected in nearest
        return expected
    assert len(nearest) == 1, (name,nearest)
    return next(iter(nearest))


class AdaptiveRationalIndependentOracleTests(unittest.TestCase):
    """Rational scalar oracle, full-coordinate tie fixtures and strict boxes.

    Tiny radii and ill-conditioned inverse frames exercise raw point mapping;
    the latter's labels need not be within GeometryAddress's storage domain.
    Continuous polygon area and the production Q40 profile are separate scopes.
    """

    def test_outward_enclosures_contain_independent_exact_scalar_points(self):
        for name,source,target,point in cases():
            exact = exact_relative(source,target,point)
            expected = expected_cell(name,exact)
            q,r,denominator = joint_ratio(point)
            kernel = compile_adaptive_pair(source,target)
            for bits in (0,4,16,32,80):
                with self.subTest(case=name,bits=bits):
                    qlo,qhi,rlo,rhi,scale = kernel.enclose_ratio(q,r,denominator,bits)
                    self.assertLessEqual(F(qlo,scale),exact[0])
                    self.assertLessEqual(exact[0],F(qhi,scale))
                    self.assertLessEqual(F(rlo,scale),exact[1])
                    self.assertLessEqual(exact[1],F(rhi,scale))
                    certified = certify_target_box(qlo,qhi,rlo,rhi,scale)
                    if certified is not None:
                        self.assertEqual(certified,expected)

    def test_final_labels_preserve_unique_distances_and_explicit_ties(self):
        for name,source,target,point in cases():
            with self.subTest(case=name):
                exact = exact_relative(source,target,point)
                q,r,denominator = joint_ratio(point)
                kernel = compile_adaptive_pair(source,target,initial_bits=16,max_bits=128)
                self.assertEqual(kernel.targets(0,0,((q,r),),denominator),
                                 (expected_cell(name,exact),))

    def test_zero_bit_budget_falls_back_on_non_dyadic_tie_and_tiny_residual(self):
        for name,source,target,point in cases():
            if name != 'non_dyadic_vertex_tie' and not name.startswith('beyond_max_bits_1/'):
                continue
            with self.subTest(case=name):
                q,r,denominator = joint_ratio(point)
                kernel = compile_adaptive_pair(source,target,initial_bits=0,max_bits=0)
                result = kernel.targets_with_stats(0,0,((q,r),),denominator)
                self.assertEqual(result.targets,(expected_cell(name,exact_relative(source,target,point)),))
                self.assertEqual(result.stats['exact_fallback'],1)
                self.assertEqual(result.stats['certified_by_bits'],{0:0})


if __name__ == '__main__':
    unittest.main()
