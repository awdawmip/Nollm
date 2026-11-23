"""Read-only probe: common world units must not define an adjacent p8 budget.

Uses one frozen distinct-twist map pair and its eight source cells.  The same
world similarity scales both affine outputs, twist centers, and radius squared;
local coordinates/anchors and twist strengths retain their original units.
No timing, production edits, retries, or approximate-output correction occur.
"""
import argparse
from collections import Counter
from dataclasses import replace
from fractions import Fraction as F
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT/'lab/nollm-lab'), str(ROOT/'packages/nollm-core/src')]

from geometry.adaptive_rational_kernel import compile_adaptive_pair
from geometry.quantized_rational_kernel import compile_quantized_pair
from geometry.rational_coverage import nearest_axial_rational, rational_sample_offsets, rational_sample_numerators
from geometry.rational_geometry import RationalLayerMap


def scale_world(mapping, factor):
    """Conjugate every radial twist by x -> factor*x and scale affine output."""
    frame = replace(mapping.frame,
                    matrix=tuple(tuple(factor*x for x in row) for row in mapping.frame.matrix),
                    origin=tuple(factor*x for x in mapping.frame.origin))
    twists = tuple(replace(twist,
                           center=tuple(factor*x for x in twist.center),
                           radius_squared=factor*factor*twist.radius_squared)
                   for twist in mapping.twists)
    return RationalLayerMap(frame, twists)


def kernel_labels(kernel, coordinates):
    return tuple(kernel.targets(q, r, rational_sample_numerators(), 36)
                 for q, r in coordinates)


def exact_labels(source, target, coordinates):
    return tuple(tuple(nearest_axial_rational(*target.inverse(source.forward((q+dq, r+dr))))
                       for dq, dr in rational_sample_offsets()) for q, r in coordinates)


def comparison(reference, candidate):
    flips = sum(a != b for refrow, row in zip(reference, candidate) for a, b in zip(refrow, row))
    fn = fp = union = tv_hits = changed_sources = 0
    for refrow, row in zip(reference, candidate):
        a, b = Counter(refrow), Counter(row)
        sa, sb = set(a), set(b)
        fn += len(sa-sb)
        fp += len(sb-sa)
        union += len(sa|sb)
        tv_hits += sum(abs(a[c]-b[c]) for c in sa|sb)//2
        changed_sources += sa != sb
    return {'sample_label_changes': flips, 'false_negative_edges': fn,
            'false_positive_edges': fp, 'union_edges': union,
            'structural_error': str(F(fn+fp, union)),
            'tv': str(F(tv_hits, 96*len(reference))),
            'sources_with_changed_target_set': changed_sources}


def histograms(rows):
    return [[[q, r, n] for (q, r), n in sorted(Counter(row).items())] for row in rows]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    benchmark = ROOT/'lab/nollm-lab/geometry/results/quantized_structure_benchmark_20261123.json'
    frozen = json.loads(benchmark.read_text())
    record = next(r for r in frozen['inventories'][0]['cases']
                  if r['scenario']['name'] == 'd2_medium_up')
    case = record['scenario']
    source, target = (RationalLayerMap.from_mapping(case[k]) for k in ('lower_map', 'upper_map'))
    coordinates = tuple(tuple(p) for p in case['coordinates'])
    reference = tuple(tuple(tuple(p) for p in row) for row in record['reference_labels'])
    baseline_p8 = kernel_labels(compile_quantized_pair(source, target, fractional_bits=8), coordinates)
    results = []
    for factor in (F(1), F(1, 256), F(1, 65536)):
        scaled_source, scaled_target = (scale_world(m, factor) for m in (source, target))
        exact = exact_labels(scaled_source, scaled_target, coordinates)
        adaptive = kernel_labels(compile_adaptive_pair(scaled_source, scaled_target, initial_bits=16), coordinates)
        quantized = kernel_labels(compile_quantized_pair(scaled_source, scaled_target, fractional_bits=8), coordinates)
        normalized_source, normalized_target = (scale_world(m, 1/factor) for m in (scaled_source, scaled_target))
        normalized = kernel_labels(compile_quantized_pair(normalized_source, normalized_target, fractional_bits=8), coordinates)
        assert exact == reference
        assert adaptive == reference
        assert (normalized_source, normalized_target) == (source, target)
        assert normalized == baseline_p8
        results.append({'common_world_scale': str(factor),
                        'exact_matches_frozen_reference': exact == reference,
                        'adaptive_matches_frozen_reference': adaptive == reference,
                        'p8_vs_exact': comparison(reference, quantized),
                        'p8_vs_original_world_units': comparison(baseline_p8, quantized),
                        'normalized_maps_exactly_original': (normalized_source, normalized_target) == (source, target),
                        'normalized_p8_labels_identical': normalized == baseline_p8,
                        'p8_hit_histograms': histograms(quantized)})
    output = {'schema': 'nollm_adjacent_p8_world_unit_probe_v1',
              'source_baseline': 'd6a3d4c39aec4df56133a4c70bc081752d5ba5a4', 'frozen_inventory_seed': 20261123,
              'case': case['name'], 'direction': 'source layer 1 to target layer 0',
              'source_twists': len(source.twists), 'target_twists': len(target.twists),
              'source_cells': len(coordinates), 'sample_count_per_source': 96,
              'coordinates': coordinates, 'source_map': source.to_mapping(), 'target_map': target.to_mapping(),
              'normalization_rule': "affine matrix and origin multiply by lambda; local anchors unchanged; twist centers multiply by lambda; radius_squared multiplies by lambda^2; strengths unchanged",
              'normalization_back_rule': 'multiply scaled world maps by 1/lambda before compiling p8',
              'baseline_p8_vs_exact': comparison(reference, baseline_p8),
              'reference_hit_histograms': histograms(reference),
              'results': results,
              'scope': 'one frozen adjacent pair, 8 cells, 768 labels; demonstrates world-unit dependence, not a general error-rate bound or production normalization implementation'}
    destination = args.output
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'output': str(destination), 'case': case['name'], 'results': [
        {k:v for k,v in row.items() if k != 'p8_hit_histograms'} for row in results]}, indent=2))


if __name__ == '__main__':
    main()
