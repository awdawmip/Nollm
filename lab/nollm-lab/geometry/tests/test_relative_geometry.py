"""Explicit relative-coordinate arithmetic and its input-precision limits."""
from collections import Counter
from dataclasses import replace
from decimal import Decimal, localcontext
import unittest

from nollm_core import GeometryAddress, coverage_sample_offsets_q40, nearest_axial_q40, normalize_q16_weights
from geometry.deformation import (
    DEFORMATION_CONTRACT_ID, LayerMap, RadialTwist, SimilarityFrame, sampled_coverage,
)
from geometry.relative_geometry import (
    RELATIVE_DEFORMATION_CONTRACT_ID, relative_layer_maps, sampled_relative_coverage,
)


def cell(layer=0, q=1, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def records(coverage):
    return tuple((m.target.q, m.target.r, m.hit_count, m.weight_q16) for m in coverage.members)


def common_translation(mapping, anchor):
    x, y = anchor
    frame = replace(mapping.frame, origin=(mapping.frame.origin[0]+x, mapping.frame.origin[1]+y))
    twists = tuple(replace(t, center=(t.center[0]+x, t.center[1]+y)) for t in mapping.twists)
    return LayerMap(frame, twists)


def decimal_axis_aligned_reference(source, source_map, target_map):
    """Evaluate accepted float inputs in 80-digit world coordinates directly.

    This reference does not recenter through the new interface. Its fixtures
    have zero angles and no twists, so all operations except sqrt(3) are exact
    decimal arithmetic on the accepted binary-float input values.
    """
    with localcontext() as context:
        context.prec = 80
        root3, two, three = Decimal(3).sqrt(), Decimal(2), Decimal(3)
        sf, tf = source_map.frame, target_map.frame
        convert = Decimal.from_float
        source_origin = tuple(convert(v) for v in sf.origin)
        target_origin = tuple(convert(v) for v in tf.origin)
        source_anchor = tuple(convert(v) for v in sf.local_anchor)
        target_anchor = tuple(convert(v) for v in tf.local_anchor)
        source_scale, target_scale = convert(float(sf.scale)), convert(float(tf.scale))
        cx = root3*(Decimal(source.q)+Decimal(source.r)/two)
        cy = three*source.r/two
        targets = []
        for oq, or_ in coverage_sample_offsets_q40():
            local = cx+Decimal(oq)/(1 << 40), cy+Decimal(or_)/(1 << 40)
            world = tuple(source_origin[i]+source_scale*(local[i]-source_anchor[i]) for i in range(2))
            target = tuple(target_anchor[i]+(world[i]-target_origin[i])/target_scale for i in range(2))
            q, r = target[0]/root3-target[1]/three, two*target[1]/three
            targets.append(nearest_axial_q40(round(q*(1 << 40)), round(r*(1 << 40))))
        counts = sorted(Counter(targets).items())
        weights = normalize_q16_weights([count for _, count in counts])
        return tuple((q, r, count, weight) for ((q, r), count), weight in zip(counts, weights))


class RelativeGeometryTests(unittest.TestCase):
    def test_large_common_anchor_counterexample_is_repaired_by_explicit_v2(self):
        source = cell()
        first, second = LayerMap.for_layer(0), LayerMap.for_layer(1)
        anchor = (2**54, 2**54)
        moved_first, moved_second = common_translation(first, anchor), common_translation(second, anchor)
        ordinary = sampled_coverage(source, 1, first, second)
        old = sampled_coverage(source, 1, moved_first, moved_second)
        new = sampled_relative_coverage(source, 1, moved_first, moved_second)
        self.assertEqual(tuple((m.target.q, m.target.r, m.hit_count) for m in old.members),
                         ((0, 0, 63), (3, -1, 33)))
        self.assertNotEqual(records(old), records(ordinary))
        self.assertEqual(records(new), records(ordinary))
        self.assertEqual(old.contract_id, DEFORMATION_CONTRACT_ID)
        self.assertEqual(new.contract_id, RELATIVE_DEFORMATION_CONTRACT_ID)

    def test_frames_and_all_world_twist_centers_follow_the_common_anchor(self):
        first = LayerMap(SimilarityFrame((4, -8), (0.25, 0.5), 1.0, 0.2),
                         (RadialTwist((4, -8), 24, 0.7), RadialTwist((-4, 8), 32, -0.3)))
        second = LayerMap(SimilarityFrame((8, 4), (-0.5, 0.25), 0.75, -0.4),
                          (RadialTwist((8, -4), 28, -0.6),))
        anchor = (2**54, -2**54)
        moved_first, moved_second = common_translation(first, anchor), common_translation(second, anchor)
        for source in (cell(0, 1, 0), cell(0, 3, -5), cell(0, -4, 7)):
            expected = sampled_relative_coverage(source, 1, first, second)
            actual = sampled_relative_coverage(source, 1, moved_first, moved_second)
            self.assertEqual(records(actual), records(expected))
            self.assertEqual(sum(m.hit_count for m in actual.members), 96)
            self.assertEqual(sum(m.weight_q16 for m in actual.members), 65536)
        a, b = relative_layer_maps(moved_first, moved_second)
        self.assertEqual(a.frame.origin, (-4, -12))
        self.assertEqual(b.frame.origin, (0, 0))
        self.assertEqual(a.frame.local_anchor, first.frame.local_anchor)
        self.assertEqual(tuple(t.center for t in a.twists), ((-4, -12), (-12, 4)))
        self.assertEqual(tuple(t.center for t in b.twists), ((0, -8),))

    def test_independent_high_precision_axis_aligned_geometry(self):
        anchor = float(2**54)
        first = LayerMap(SimilarityFrame((anchor+4, anchor-8), (0.25, -0.5), 0.5))
        second = LayerMap(SimilarityFrame((anchor, anchor), (-0.5, 0.25), 1.25))
        for source in (cell(0, 1, 0), cell(0, 3, -5), cell(0, -7, 4)):
            actual = sampled_relative_coverage(source, 1, first, second)
            self.assertEqual(records(actual), decimal_axis_aligned_reference(source, first, second))

    def test_ordinary_nonboundary_coverage_and_source_maps_are_preserved(self):
        first = LayerMap(SimilarityFrame((0.5, -0.25), scale=1.0, angle=0.3),
                         (RadialTwist((1, -2), 7, 0.4),))
        second = LayerMap(SimilarityFrame((-0.25, 0.5), scale=0.8, angle=-0.2))
        before = first.to_mapping(), second.to_mapping()
        for source in (cell(0, 3, -5), cell(0, -11, 9), cell(0, 8, 2)):
            actual = sampled_relative_coverage(source, 1, first, second)
            self.assertEqual(records(actual), records(sampled_coverage(source, 1, first, second)))
            self.assertEqual(actual.to_mapping()['contract_id'], RELATIVE_DEFORMATION_CONTRACT_ID)
        self.assertEqual((first.to_mapping(), second.to_mapping()), before)

    def test_input_offsets_already_rounded_away_cannot_be_recovered(self):
        anchor = 2**54
        rounded = LayerMap(SimilarityFrame((anchor+1, anchor)))
        target = LayerMap(SimilarityFrame((anchor, anchor)))
        a, b = relative_layer_maps(rounded, target)
        self.assertEqual(a.frame.origin, (0, 0))
        self.assertEqual(b.frame.origin, (0, 0))
        accepted = sampled_relative_coverage(cell(), 1, rounded, target)
        retained = sampled_relative_coverage(cell(), 1,
                                             LayerMap(SimilarityFrame((1, 0))), LayerMap())
        self.assertNotEqual(records(accepted), records(retained))

    def test_finite_world_inputs_with_unrepresentable_difference_raise(self):
        first = LayerMap(SimilarityFrame((1e308, 0)))
        second = LayerMap(SimilarityFrame((-1e308, 0)))
        with self.assertRaisesRegex(ValueError, 'relative world coordinates'):
            sampled_relative_coverage(cell(), 1, first, second)
        first = LayerMap(SimilarityFrame((-1e308, 0)),
                         (RadialTwist((1e308, 0), 1, 0.5),))
        with self.assertRaisesRegex(ValueError, 'relative world coordinates'):
            relative_layer_maps(first, second)


if __name__ == '__main__':
    unittest.main()
