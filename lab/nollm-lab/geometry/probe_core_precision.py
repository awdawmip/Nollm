"""Audit only: reduce final target-coordinate precision in the existing Q40 Core.

The compiled constants and all map calculations stay unchanged. Only the final
target q/r sample coordinates are rounded half-even to p binary fractional
bits before the existing cube-nearest rule. This is not coefficient, parameter,
floating-point-mantissa or per-operation precision reduction.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import json
import os
from pathlib import Path
import platform
import sys
from time import perf_counter


ROOT = Path(os.environ.get('NOLLM_REPO', Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(ROOT / 'packages/nollm-core/src'))
from nollm_core import (
    ACTIVE_APPROXIMATION_POLICY, GeometryAddress, coverage_stencil_q40,
    expand_physical_coverage, nearest_axial_q40,
)


PRECISIONS = tuple(range(41))
SCALE = 1 << 40
MAX_ACTIVE_HEX_RADIUS = ACTIVE_APPROXIMATION_POLICY.storage_hex_radius
SOURCE_COMMIT = '0e7ddd99bc5a07948ad74b4856899581a6657bc1'
AXES = ((1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1))


def round_ratio(numerator, denominator):
    sign = -1 if numerator < 0 else 1
    whole, remainder = divmod(abs(numerator), denominator)
    if 2*remainder > denominator or (2*remainder == denominator and whole % 2):
        whole += 1
    return sign*whole


def hex_radius(q, r):
    return max(abs(q), abs(r), abs(q+r))


def coordinates(direction):
    local = [(q, r) for q in range(-8, 9) for r in range(-8, 9)
             if hex_radius(q, r) <= 8]
    million = [(a*1_000_000+dq, b*1_000_000+dr) for a, b in AXES
               for dq in range(-2, 3) for dr in range(-2, 3)]
    large = []
    anchor_radii = []
    for q, r in AXES:
        unit = GeometryAddress('default_dream_v1', 'default', 0, q, r)
        out_q, out_r = coverage_stencil_q40(unit, direction).center_q40
        expansion = hex_radius(out_q, out_r)
        # Leave 64 cells at both domains' boundary for stencil and +/-2 jitter.
        radius = min(MAX_ACTIVE_HEX_RADIUS-64,
                     ((MAX_ACTIVE_HEX_RADIUS-64)*SCALE)//expansion)
        anchor_radii.append(radius)
        large.extend((q*radius+dq, r*radius+dr)
                     for dq in range(-2, 3) for dr in range(-2, 3))
    return [('local_radius_8', local), ('around_signed_million', million),
            ('near_admitted_boundary', large)], anchor_radii


def empty_stats():
    return {'cases': 0, 'samples': 0, 'target_set_changed_cases': 0,
            'histogram_changed_cases': 0, 'sample_label_changes': 0,
            'max_target_hit_error': 0, 'max_case_l1_hit_error': 0,
            'sum_case_l1_hit_error': 0, 'domain_invalid_cases': 0,
            'first_target_set_change': None, 'first_histogram_change': None}


def add(stats, ref, labels, source, direction):
    baseline, observed = Counter(ref), Counter(labels)
    target_changed = set(baseline) != set(observed)
    histogram_changed = baseline != observed
    errors = [abs(baseline[key]-observed[key]) for key in set(baseline) | set(observed)]
    stats['cases'] += 1
    stats['samples'] += len(ref)
    stats['target_set_changed_cases'] += int(target_changed)
    stats['histogram_changed_cases'] += int(histogram_changed)
    stats['sample_label_changes'] += sum(a != b for a, b in zip(ref, labels))
    stats['max_target_hit_error'] = max(stats['max_target_hit_error'], max(errors, default=0))
    stats['max_case_l1_hit_error'] = max(stats['max_case_l1_hit_error'], sum(errors))
    stats['sum_case_l1_hit_error'] += sum(errors)
    stats['domain_invalid_cases'] += int(any(hex_radius(*p) > MAX_ACTIVE_HEX_RADIUS for p in labels))
    witness = {'source_qr': list(source), 'direction': direction,
               'reference': [[q, r, n] for (q, r), n in sorted(baseline.items())],
               'reduced': [[q, r, n] for (q, r), n in sorted(observed.items())]}
    if target_changed and stats['first_target_set_change'] is None:
        stats['first_target_set_change'] = witness
    if histogram_changed and stats['first_histogram_change'] is None:
        stats['first_histogram_change'] = witness


def finish(stats):
    result = dict(stats)
    result['max_target_share_error'] = str(Fraction(stats['max_target_hit_error'], 96))
    result['max_case_total_variation'] = str(Fraction(stats['max_case_l1_hit_error'], 192))
    result['mean_case_total_variation'] = str(Fraction(stats['sum_case_l1_hit_error'], 192*stats['cases']))
    return result


def stable_suffix(rows, metric):
    """First p after which every tested p through 40 passes; not global minimum."""
    failures = [row['fractional_bits'] for row in rows if row[metric]]
    return max(failures)+1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'lab/nollm-lab/geometry/results/core_precision_probe_20261122.json')
    args = parser.parse_args()
    started = perf_counter()
    total = {p: empty_stats() for p in PRECISIONS}
    groups, inventory = [], []
    min_positive_slack, boundary_samples = None, 0
    reference_max_radius = 0
    for direction in ('coverage_up', 'coverage_down'):
        point_groups, anchor_radii = coordinates(direction)
        for group_name, sources in point_groups:
            group = {p: empty_stats() for p in PRECISIONS}
            for q, r in sources:
                source = GeometryAddress('default_dream_v1', 'default', 0, q, r)
                actual = expand_physical_coverage(source, direction)
                stencil = coverage_stencil_q40(source, direction)
                center_q, center_r = stencil.center_q40
                points = tuple((center_q+dq, center_r+dr) for dq, dr in stencil.offsets_q40)
                ref = tuple(nearest_axial_q40(a, b) for a, b in points)
                assert Counter(ref) == Counter({(m.target.q, m.target.r): m.hit_count for m in actual.members})
                reference_max_radius = max(reference_max_radius, *(hex_radius(*target) for target in ref))
                for (a, b), (x, y) in zip(points, ref):
                    dq, dr = a-x*SCALE, b-y*SCALE
                    slack = min(SCALE-abs(2*dq+dr), SCALE-abs(dq+2*dr), SCALE-abs(dr-dq))
                    assert slack >= 0
                    if slack == 0:
                        boundary_samples += 1
                    else:
                        min_positive_slack = slack if min_positive_slack is None else min(min_positive_slack, slack)
                for p in PRECISIONS:
                    divisor = 1 << (40-p)
                    labels = tuple(nearest_axial_q40(round_ratio(a, divisor)*divisor,
                                                     round_ratio(b, divisor)*divisor)
                                   for a, b in points)
                    add(group[p], ref, labels, (q, r), direction)
                    add(total[p], ref, labels, (q, r), direction)
            rows = [{'fractional_bits': p, **finish(group[p])} for p in PRECISIONS]
            groups.append({'name': group_name, 'direction': direction, 'rows': rows,
                           'observed_stable_suffix_target_set': stable_suffix(rows, 'target_set_changed_cases'),
                           'observed_stable_suffix_histogram': stable_suffix(rows, 'histogram_changed_cases'),
                           'observed_stable_suffix_labels': stable_suffix(rows, 'sample_label_changes')})
            inventory.append({'name': group_name, 'direction': direction, 'coordinates': sources,
                              'near_boundary_anchor_radii': anchor_radii if group_name == 'near_admitted_boundary' else None})
    rows = [{'fractional_bits': p, **finish(total[p])} for p in PRECISIONS]
    assert all(row['domain_invalid_cases'] == 0 for row in rows)
    assert rows[-1]['sample_label_changes'] == 0
    output = {'schema': 'nollm_core_precision_probe_v1',
              'scope': 'finite admitted Core source cells; final target-coordinate quantization only',
              'source_commit': SOURCE_COMMIT, 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
              'python': sys.version, 'platform': platform.platform(),
              'operation': 'round only final target q/r Q40 coordinates to p fractional bits, half-even; preserve original nearest-cell tie rules',
              'comparison_basis': 'existing compiled Q40 Core, not ideal real rotation/scale or continuous area',
              'precision_scan': list(PRECISIONS), 'samples_per_case': 96,
              'rows': rows, 'groups': groups, 'input_inventory': inventory,
              'source_and_target_domain': {'max_admitted_hex_radius': MAX_ACTIVE_HEX_RADIUS,
                                           'reference_max_target_radius': reference_max_radius,
                                           'excluded_cases': 0, 'all_reduced_target_domains_valid': True},
              'boundary_margin': {'exact_face_boundary_samples': boundary_samples,
                                   'min_positive_projection_slack_q40': min_positive_slack,
                                   'min_positive_projection_slack': str(Fraction(min_positive_slack, SCALE))},
              'observed_stable_suffix': {
                  'target_set': stable_suffix(rows, 'target_set_changed_cases'),
                  'histogram': stable_suffix(rows, 'histogram_changed_cases'),
                  'labels': stable_suffix(rows, 'sample_label_changes')},
              'elapsed_seconds': perf_counter()-started,
              'limitations': ['finite deterministic inventory, no exhaustive residue enumeration',
                              'a zero-mismatch p can be followed by a mismatching higher p',
                              'p=40 is identity for final Q40 coordinates; this does not justify reducing matrix constants',
                              'no runtime speedup measured; coordinates were first computed exactly']}
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
    main_rows = [{k: row[k] for k in ('fractional_bits', 'cases', 'samples', 'target_set_changed_cases',
                                     'histogram_changed_cases', 'sample_label_changes', 'max_target_share_error')}
                 for row in rows if row['fractional_bits'] in (4, 6, 8, 10, 12, 16, 20, 24, 32, 40)]
    print(json.dumps({'rows': main_rows, 'observed_stable_suffix': output['observed_stable_suffix'],
                      'boundary_margin': output['boundary_margin'], 'domain': output['source_and_target_domain'],
                      'groups': [{k: value for k, value in g.items() if k != 'rows'} for g in groups],
                      'elapsed_seconds': output['elapsed_seconds']}, indent=2))


if __name__ == '__main__':
    main()
