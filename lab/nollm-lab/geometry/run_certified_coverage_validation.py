"""Bounded, reproducible Lab comparison; all generated output stays outside Git."""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction as F
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from certified_overlap import METHOD, certify_coverage  # noqa: E402
from broad_residue import broad_exact_fixtures  # noqa: E402
from oracle_decimal import coverage as decimal_coverage  # noqa: E402
from nollm_core import GeometryAddress, UnsupportedPhysicalCoverage, expand_physical_coverage  # noqa: E402


NUMERIC_CROSSCHECK_TOLERANCE = F(1,10**60)
ENCLOSURE_TOLERANCE = F(1,1<<64)
DIAGNOSTIC_ERROR_BUDGET = F(1,20)  # Diagnostic, not a new product invariant.


def _wire(lo: F, hi: F) -> dict[str,int]:
    """Outward-round report endpoints; display floats never certify anything."""
    s = 1 << 96
    a,b = lo*s,hi*s
    return {'lower_n':a.numerator//a.denominator,
            'upper_n':-((-b.numerator)//b.denominator),'denominator':s}


def validate(per_phase_direction: int = 128) -> dict[str,object]:
    if type(per_phase_direction) is not int or not 1 <= per_phase_direction <= 128:
        raise ValueError('per_phase_direction must lie in [1,128]')
    fixtures = broad_exact_fixtures(per_phase_direction)
    cases, tvs, missed, mismatches = [],[],[],[]
    bits_used, candidates, quality = Counter(),Counter(),Counter()
    boundary_errors = unresolved = definite_misses = 0
    for fixture in fixtures:
        layer,q,r,direction = fixture.layer,fixture.q,fixture.r,fixture.direction
        certified = certify_coverage(layer,q,r,direction,tolerance=ENCLOSURE_TOLERANCE)
        delta = 1 if direction == 'coverage_down' else -1
        numerical = {(m.q,m.r):F(m.source_share) for m in decimal_coverage(layer,q,r,layer+delta,4)}
        shares = certified.shares()
        for key in sorted(shares.keys() | numerical.keys()):
            lo,hi = shares.get(key,(F(0),F(0)))
            value = numerical.get(key,F(0))
            if not lo-NUMERIC_CROSSCHECK_TOLERANCE <= value <= hi+NUMERIC_CROSSCHECK_TOLERANCE:
                mismatches.append({'layer':layer,'q':q,'r':r,'direction':direction,'target':key})
        bits_used[certified.precision_bits] += 1
        candidates[certified.candidate_count] += 1
        unresolved += sum(m.lower == 0 for m in certified.members)
        case = {'layer':layer,'q':q,'r':r,'direction':direction,
                'bucket':fixture.coordinate_bucket,'precision_bits':certified.precision_bits,
                'candidate_count':certified.candidate_count,
                'shares':[{'q':m.q,'r':m.r,'classification':m.classification,
                           'source_share':_wire(m.lower,m.upper)} for m in certified.members],
                'partition_sum':_wire(certified.total_lower,certified.total_upper)}
        try:
            approximate = expand_physical_coverage(GeometryAddress('default_dream_v1','default',layer,q,r),direction)
        except UnsupportedPhysicalCoverage:
            boundary_errors += 1
            case['production_status'] = 'storage_boundary_rejected'
            cases.append(case)
            continue
        weights = {(m.target.q,m.target.r):m.weight_q16 for m in approximate.members}
        error = certified.compare_q16(weights)
        tvs.append(error['total_variation']); missed.append(error['missed_mass'])
        definite_misses += sum(m.lower>0 and weights.get((m.q,m.r),0)==0 for m in certified.members)
        lo,hi = error['total_variation']
        status = ('within_budget' if hi<=DIAGNOSTIC_ERROR_BUDGET else
                  'above_budget' if lo>DIAGNOSTIC_ERROR_BUDGET else 'undecided')
        quality[status] += 1
        case.update({'production_status':'compared','diagnostic_1_over_20':status,
                     'errors':{k:_wire(*v) for k,v in error.items()},
                     'production_q16':[[q,r,w] for (q,r),w in sorted(weights.items())]})
        cases.append(case)
    summary = {'fixture_count':len(fixtures),'production_compared':len(tvs),
               'production_boundary_rejected':boundary_errors,
               'precision_distribution':dict(sorted(bits_used.items())),
               'candidate_distribution':dict(sorted(candidates.items())),
               'unresolved_support_members':unresolved,'definitely_missed_members':definite_misses,
               'diagnostic_1_over_20':dict(sorted(quality.items())),
               'numeric_crosscheck_mismatches':len(mismatches)}
    for name,values in (('total_variation',tvs),('missed_mass',missed)):
        if values:
            lo,hi = max(x[0] for x in values),max(x[1] for x in values)
            summary['max_'+name] = _wire(lo,hi)
            summary['display_max_'+name] = [float(lo),float(hi)]
    return {'schema':METHOD,'fixture_seed':'0xca01d39',
            'per_phase_direction':per_phase_direction,'summary':summary,
            'passed':not mismatches and len(cases)==len(fixtures),
            'limits':['Lab only; production geometry and state are unchanged',
                      'Per-request interval certificates, not a whole-domain quality theorem',
                      'Decimal is a numerical cross-check, not the certificate source',
                      'A tight oracle interval is not a small production approximation error',
                      'The 1/20 error budget is diagnostic, not a product acceptance change'],
            'mismatches':mismatches,'cases':cases}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--per-phase-direction',type=int,default=128)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(HERE.parents[2]):
        parser.error('generated output must be outside the repository')
    result = validate(args.per_phase_direction)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps(result['summary'],sort_keys=True,indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
