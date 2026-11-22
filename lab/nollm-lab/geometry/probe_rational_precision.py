"""Measure final-coordinate quantization under the new rational Lab contract.

The maps are evaluated exactly first. This diagnoses precision requirements;
it neither reduces intermediate nonlinear cost nor measures runtime speedup.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from fractions import Fraction as F
from math import lcm
from pathlib import Path
import json
import platform
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'packages/nollm-core/src'), str(ROOT / 'lab/nollm-lab')]

from geometry.precision_budget import (
    certify_axial_ratio, minimum_safe_fraction_bits, quantize_axial_ratio,
)
from geometry.rational_affine_kernel import compile_affine_pair, nearest_axial_ratio
from geometry.rational_coverage import rational_sample_numerators, rational_sample_offsets
from geometry.rational_geometry import RationalAffine, RationalLayerMap, RationalRadialTwist

BITS = tuple(range(65))
CERTIFICATE_BITS = (8, 12, 16, 20)
SOURCE_COMMIT = '0e7ddd99bc5a07948ad74b4856899581a6657bc1'


def joint_ratio(q, r):
    d = lcm(q.denominator, r.denominator)
    return q.numerator * (d // q.denominator), r.numerator * (d // r.denominator), d


def exact_points(source, target, q, r):
    kernel = compile_affine_pair(source, target)
    if kernel is not None:
        return tuple(kernel.map_ratio(36*q+dq, 36*r+dr, 36)
                     for dq, dr in rational_sample_numerators())
    return tuple(joint_ratio(*target.inverse(source.forward((q+dq, r+dr))))
                 for dq, dr in rational_sample_offsets())


def groups():
    coordinates = tuple((q, r) for q in range(-4, 4) for r in range(-4, 4))
    sf = RationalAffine.similarity('5/4', '1/7', origin=('1/11', '-2/13'))
    tf = RationalAffine.similarity('7/6', '-1/9', origin=('-1/5', '2/7'),
                                   local_anchor=('1/13', '-1/17'))
    yield 'affine_64', RationalLayerMap(sf), RationalLayerMap(tf), coordinates
    anchor = 2**160
    yield ('common_anchor_2_pow_160_64',
           RationalLayerMap(replace(sf, origin=(anchor+1, -anchor))),
           RationalLayerMap(replace(tf, origin=(anchor, -anchor))), coordinates)
    first = RationalRadialTwist((0, 0), 25, '1/5')
    second = RationalRadialTwist(('1/5', 0), 25, '-1/7')
    yield ('distinct_twists_16', RationalLayerMap(sf, (first,)),
           RationalLayerMap(tf, (second,)), coordinates[24:40])
    nearby = tuple((q, r) for q in range(-1, 2) for r in range(-1, 2)
                   if max(abs(q), abs(r), abs(q+r)) <= 1)
    yield ('two_center_chain_7', RationalLayerMap(sf, (first, second)),
           RationalLayerMap(tf), nearby)
    # Make exactly one original sample cross the (0,0)/(1,0) face by delta.
    small = RationalAffine.similarity('1/10', '1/7')
    moved = tuple(small.forward(p) for p in rational_sample_offsets())
    tip = max(moved, key=lambda p: 2*p[0]+p[1])
    assert sum(2*q+r == 2*tip[0]+tip[1] for q, r in moved) == 1
    for exponent in (20, 40, 60):
        frame = replace(small, origin=(F(1, 2)-tip[0]+F(1, 1 << exponent), -tip[1]))
        yield (f'one_hit_edge_delta_2_pow_minus_{exponent}', RationalLayerMap(frame),
               RationalLayerMap(), ((0, 0),))


def audit_group(name, source, target, coordinates):
    cases, bit_requirements, boundary_points = [], [], 0
    for q, r in coordinates:
        points = exact_points(source, target, q, r)
        labels = tuple(nearest_axial_ratio(*point) for point in points)
        if name.startswith('one_hit_edge'):
            assert Counter(labels) == Counter({(0, 0): 95, (1, 0): 1})
        cases.append((points, labels, Counter(labels)))
        for point in points:
            required = minimum_safe_fraction_bits(*point)
            if required is None:
                boundary_points += 1
            else:
                bit_requirements.append(required)
    rows = []
    for bits in BITS:
        row = {'fractional_bits': bits, 'target_set_changed_cases': 0,
               'histogram_changed_cases': 0, 'sample_label_changes': 0,
               'max_target_hit_error': 0}
        unresolved, wrong_certificates = 0, 0
        error = F(1, 1 << (bits+1))
        for points, expected, baseline in cases:
            rounded = tuple(quantize_axial_ratio(*point, bits) for point in points)
            labels = tuple(nearest_axial_ratio(*point) for point in rounded)
            observed = Counter(labels)
            row['target_set_changed_cases'] += set(observed) != set(baseline)
            row['histogram_changed_cases'] += observed != baseline
            row['sample_label_changes'] += sum(a != b for a, b in zip(labels, expected))
            row['max_target_hit_error'] = max(row['max_target_hit_error'],
                max(abs(observed[c]-baseline[c]) for c in set(observed) | set(baseline)))
            if bits in CERTIFICATE_BITS:
                for point, label in zip(rounded, expected):
                    certified = certify_axial_ratio(*point, error_q=error)
                    unresolved += certified is None
                    wrong_certificates += certified is not None and certified != label
        row['max_target_share_error'] = str(F(row['max_target_hit_error'], 96))
        if bits in CERTIFICATE_BITS:
            assert wrong_certificates == 0
            row['uncertified_samples'] = unresolved
            row['wrong_certificates'] = wrong_certificates
        rows.append(row)
    suffix = {}
    for metric in ('target_set_changed_cases', 'histogram_changed_cases', 'sample_label_changes'):
        failed = [r['fractional_bits'] for r in rows if r[metric]]
        suffix[metric] = max(failed)+1 if failed and max(failed) < BITS[-1] else None if failed else 0
    return {'name': name, 'cases': len(cases), 'samples': 96*len(cases),
            'source_map': source.to_mapping(), 'target_map': target.to_mapping(),
            'source_coordinates': coordinates, 'rows': rows,
            'observed_stable_suffix_through_64': suffix,
            'strict_boundary_samples': boundary_points,
            'max_interior_certificate_bits': max(bit_requirements, default=None),
            'whole_group_strict_certificate_bits': None if boundary_points else max(bit_requirements)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'lab/nollm-lab/geometry/results/rational_precision_probe_20261122.json')
    args = parser.parse_args()
    outputs = [audit_group(*group) for group in groups()]
    q, r, d = 10, 9, 30  # (1/3, 3/10): deterministic success is not monotone in p.
    non_monotone = {'point': ['1/3', '3/10'], 'reference': nearest_axial_ratio(q, r, d),
                    'certificate_bits': minimum_safe_fraction_bits(q, r, d),
                    'labels': [{'bits': p, 'label': nearest_axial_ratio(*quantize_axial_ratio(q, r, d, p))}
                               for p in range(9)]}
    result = {'schema': 'nollm_rational_precision_probe_v1', 'source_commit': SOURCE_COMMIT,
              'generated_at_utc': datetime.now(timezone.utc).isoformat(),
              'python': sys.version, 'platform': platform.platform(),
              'operation': 'exact map first, then half-even final target q/r quantization',
              'precision_scan': BITS, 'groups': outputs, 'non_monotone_example': non_monotone,
              'limitations': ['finite explicit input maps; original Core and continuous area are different contracts',
                              'final-coordinate certificates require valid total error bounds if used with low-precision map arithmetic',
                              'no end-to-end speedup measured; exact nonlinear map evaluation still occurs']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'groups': [{k: v for k, v in group.items() if k not in
          ('source_map', 'target_map', 'source_coordinates', 'rows')} | {
              'selected_rows': [r for r in group['rows'] if r['fractional_bits'] in (8, 10, 12, 14, 16, 20, 40, 60, 61)]}
          for group in outputs], 'non_monotone_example': non_monotone}, indent=2))


if __name__ == '__main__':
    main()
