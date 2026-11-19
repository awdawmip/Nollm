"""Fit seven existing topic entrances to a fixed patch using host placement intentions."""
import argparse
from collections import Counter
from functools import lru_cache
from itertools import permutations
import json
from pathlib import Path

from vertical_atlas import HERE, REPO, SOURCE_REVISION, build, coords, intent, topic_cells
from nollm_core import expand_physical_coverage


def fit():
    original = topic_cells()
    topics = tuple(original)
    sites = tuple(original.values())
    support = [dict(expand_physical_coverage(site, "coverage_down").targets()) for site in sites]
    memberships = {
        cell: sum(1 << i for i, footprint in enumerate(support) if cell in footprint)
        for footprint in support for cell in footprint
    }
    role_patterns = Counter(tuple(topics.index(topic) for topic in intended) for intended in intent().values())

    @lru_cache(maxsize=None)
    def fit_leaf(home, wanted):
        # Same leaf choice as the baseline: maximize intended contexts, minimize
        # accidental ones, then prefer the strongest primary overlap and stable address.
        def priority(cell):
            mask = memberships[cell]
            return (-(mask & wanted).bit_count(), (mask & ~wanted).bit_count(),
                    -support[home][cell], cell.stable_key())

        cell = min(support[home], key=priority)
        mask = memberships[cell]
        return (wanted & ~mask).bit_count(), (mask & ~wanted).bit_count(), support[home][cell]

    def measure(assignment):
        missed = extra = home_weight = 0
        for pattern, multiplicity in role_patterns.items():
            mask = sum(1 << assignment[t] for t in pattern)
            absent, accidental, weight = fit_leaf(assignment[pattern[0]], mask)
            missed += absent * multiplicity
            extra += accidental * multiplicity
            home_weight += weight * multiplicity
        return {"missed_intents": missed, "unintended_incidences": extra,
                "primary_weight_q16_sum": home_weight, "disagreements": missed + extra}

    def objective(assignment):
        trial = measure(assignment)
        return trial["disagreements"], -trial["primary_weight_q16_sum"], assignment

    baseline = tuple(range(len(sites)))
    chosen = min(permutations(baseline), key=objective)
    site_map = {key: sites[index] for key, index in zip(topics, chosen)}
    return site_map, {
        "objective": "Minimize missed intended incidences plus unintended incidences across all reviewed files. Break ties by largest sum of home weights, then baseline site index order.",
        "intended_incidences": sum(len(pattern) * count for pattern, count in role_patterns.items()),
        "arrangements": 5040, "baseline": measure(baseline), "fitted": measure(chosen),
        "fitted_sites": {key: coords(cell) for key, cell in site_map.items()},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, help="write a new native field using the fitted entrances")
    parser.add_argument("--volume", type=Path, default=HERE / "aoci/aoci.code.txt")
    parser.add_argument("--repo", type=Path, default=REPO)
    args = parser.parse_args()
    sites, result = fit()
    if args.field:
        build(args.repo, SOURCE_REVISION, args.volume, args.field, sites=sites)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
