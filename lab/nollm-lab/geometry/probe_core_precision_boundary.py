"""Construct admitted Core counterexamples by exact face-projection congruences."""
import argparse
from collections import Counter
from math import gcd
from pathlib import Path
import json
import os
import sys

ROOT = Path(os.environ.get('NOLLM_REPO', Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(ROOT / 'packages/nollm-core/src'))
from nollm_core import (
    ACTIVE_APPROXIMATION_POLICY, GeometryAddress, UnsupportedPhysicalCoverage,
    coverage_stencil_q40, expand_physical_coverage, nearest_axial_q40,
)

S = 1 << 40
RADIUS = ACTIVE_APPROXIMATION_POLICY.storage_hex_radius
SOURCE_RADIUS = ACTIVE_APPROXIMATION_POLICY.active_writable_hex_radius


def cell(q, r):
    return GeometryAddress('default_dream_v1', 'default', 0, q, r)


def radius(q, r):
    return max(abs(q), abs(r), abs(q+r))


def round_ratio(n, d):
    sign = -1 if n < 0 else 1
    k, rem = divmod(abs(n), d)
    return sign*(k+int(2*rem > d or (2*rem == d and k % 2)))


def counted(points, p):
    step = 1 << (40-p)
    return Counter(nearest_axial_q40(round_ratio(q, step)*step,
                                    round_ratio(r, step)*step) for q, r in points)


def mapping(counts):
    return [[q, r, n] for (q, r), n in sorted(counts.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'lab/nollm-lab/geometry/results/core_precision_boundary_witness_20261122.json')
    args = parser.parse_args()
    witnesses = {}
    histogram39 = None
    pool = []
    tested = set()
    rejected_domain = 0
    for direction in ('coverage_up', 'coverage_down'):
        aq, ar = coverage_stencil_q40(cell(1, 0), direction).center_q40
        bq, br = coverage_stencil_q40(cell(0, 1), direction).center_q40
        offsets = coverage_stencil_q40(cell(0, 0), direction).offsets_q40
        for fq, fr in ((2, 1), (1, 2), (-1, 1)):
            a, b = fq*aq+fr*ar, fq*bq+fr*br
            projections = [fq*q+fr*r for q, r in offsets]
            extremes = (min(range(96), key=projections.__getitem__),
                        max(range(96), key=projections.__getitem__))
            solve_r = gcd(b, S) <= gcd(a, S)
            solved, scanned = (b, a) if solve_r else (a, b)
            g = gcd(solved, S)
            modulus = S//g
            inv = pow(solved//g, -1, modulus)
            for sample in extremes:
                offset = projections[sample]
                for residual in (-1, 1, -2, 2, -3, 3, 0):
                    for small in range(-2048, 2049):
                        rhs = residual-offset-scanned*small
                        if rhs % g:
                            continue
                        large = (rhs//g*inv) % modulus
                        if large > modulus//2:
                            large -= modulus
                        q, r = (small, large) if solve_r else (large, small)
                        if radius(q, r) > SOURCE_RADIUS-4:
                            continue
                        key = direction, q, r
                        if key in tested:
                            continue
                        tested.add(key)
                        source = cell(q, r)
                        try:
                            full = expand_physical_coverage(source, direction)
                        except UnsupportedPhysicalCoverage:
                            rejected_domain += 1
                            continue
                        stencil = coverage_stencil_q40(source, direction)
                        cq, cr = stencil.center_q40
                        points = tuple((cq+dq, cr+dr) for dq, dr in offsets)
                        reference = Counter({(m.target.q, m.target.r): m.hit_count for m in full.members})
                        assert reference == counted(points, 40)
                        coarse39 = counted(points, 39)
                        if coarse39 == reference:
                            continue
                        if any(radius(a, b) > RADIUS for a, b in coarse39):
                            rejected_domain += 1
                            continue
                        record = {'source_qr': [q, r], 'direction': direction,
                                  'constructed_sample': sample, 'face_form': [fq, fr],
                                  'residue_mod_q40': residual,
                                  'source_radius': radius(q, r),
                                  'reference': mapping(reference), 'p39': mapping(coarse39),
                                  'p39_target_set_changed': set(coarse39) != set(reference),
                                  'changed_labels_p39': [i for i, (a, b) in enumerate(points)
                                     if nearest_axial_q40(a, b) != nearest_axial_q40(round_ratio(a, 2)*2, round_ratio(b, 2)*2)]}
                        if histogram39 is None:
                            histogram39 = record
                            print(json.dumps({'first_p39_histogram_witness': record}), flush=True)
                        if record['p39_target_set_changed'] and 39 not in witnesses:
                            print(json.dumps({'first_p39_target_set_witness': record}), flush=True)
                        pool.append(record)
                        for p in range(40):
                            if p in witnesses:
                                continue
                            coarse = counted(points, p)
                            if set(coarse) != set(reference) and all(radius(*x) <= RADIUS for x in coarse):
                                witnesses[p] = {'pool_index': len(pool)-1, 'reduced': mapping(coarse)}
                        if len(witnesses) == 40:
                            break
                    if len(witnesses) == 40: break
                if len(witnesses) == 40: break
            if len(witnesses) == 40: break
        if len(witnesses) == 40: break
    assert len(witnesses) == 40, 'Every lower fractional precision needs a replayable witness'
    result = {'schema': 'nollm_core_precision_boundary_witness_v1',
              'source_commit': '0e7ddd99bc5a07948ad74b4856899581a6657bc1',
              'scope': 'final Q40 target q/r coordinates rounded half-even to p fractional bits',
              'source_radius_limit': SOURCE_RADIUS, 'target_storage_radius_limit': RADIUS,
              'constructed_candidates_checked': len(tested), 'domain_rejected': rejected_domain,
              'p39_histogram_witness': histogram39, 'witness_pool': pool,
              'target_set_witness_by_precision': witnesses,
              'unwitnessed_precisions': [p for p in range(40) if p not in witnesses],
              'p40_identity': 'For all integer Q40 coordinates, rounding to p40 changes no value.'}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'completed': True, 'tested_candidates': len(tested),
                      'pool': len(pool), 'unwitnessed_precisions': result['unwitnessed_precisions'],
                      'file': str(args.output)}), flush=True)


if __name__ == '__main__':
    main()
