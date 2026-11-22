"""Evaluate explicit Lab layer maps and exact Q40 translation reuse."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Direct checkout use and a packaged runtime both load the same implementation.
core_source = Path(__file__).resolve().parents[3] / "packages/nollm-core/src"
if core_source.is_dir():
    sys.path.insert(0, str(core_source))

from nollm_core import GeometryAddress
from deformation import DEFORMATION_CONTRACT_ID, LayerMap, RadialTwist, sampled_coverage
from motion import MOTION_CONTRACT_ID, TranslationFootprint


def _source(value):
    layer, q, r = value
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    motion = commands.add_parser("motion", help="compare incremental and full 96-point translation")
    motion.add_argument("--source", nargs=3, type=int, default=(0, 19, -17), metavar=("L", "Q", "R"))
    motion.add_argument("--direction", choices=("coverage_up", "coverage_down"), default="coverage_up")
    motion.add_argument("--delta-q40", nargs=2, type=int, required=True, metavar=("DQ", "DR"))
    deform = commands.add_parser("coverage", help="sample coverage through explicit invertible layer maps")
    deform.add_argument("--source", nargs=3, type=int, default=(0, 1, 0), metavar=("L", "Q", "R"))
    deform.add_argument("--target-layer", type=int, default=1)
    deform.add_argument("--source-map", type=Path, help="JSON LayerMap; otherwise the default layer map")
    deform.add_argument("--target-map", type=Path, help="JSON LayerMap; otherwise the default layer map")
    deform.add_argument("--twist", nargs=4, type=float, metavar=("CX", "CY", "RADIUS", "RADIANS"),
                        help="append a world-space twist to the target map")
    deform.add_argument("--reanchor", nargs=2, type=float, metavar=("X", "Y"),
                        help="passively re-express the target similarity's local anchor")
    args = parser.parse_args(argv)
    source = _source(args.source)
    if args.command == "motion":
        initial = TranslationFootprint.from_source(source, args.direction)
        fast = initial.translate(tuple(args.delta_q40))
        full = initial.translate(tuple(args.delta_q40), mode="full")
        result = {"contract_id": MOTION_CONTRACT_ID, "source": source.to_mapping(),
                  "direction": args.direction, "delta_q40": args.delta_q40,
                  "mode": fast.mode, "round_calls": fast.round_calls,
                  "full_round_calls": full.round_calls, "changed_samples": fast.changed_samples,
                  "matches_full": (fast.footprint.sample_targets() == full.footprint.sample_targets()
                                   and fast.footprint.counts_q16() == full.footprint.counts_q16()),
                  "members_q16": fast.footprint.counts_q16()}
    else:
        load = lambda path, layer: (LayerMap.from_mapping(json.loads(path.read_text(encoding="utf-8")))
                                    if path else LayerMap.for_layer(layer))
        source_map = load(args.source_map, source.layer)
        target_map = load(args.target_map, args.target_layer)
        if args.twist:
            x, y, radius, angle = args.twist
            target_map = target_map.with_twist(RadialTwist((x, y), radius, angle))
        if args.reanchor:
            target_map = target_map.reanchor(tuple(args.reanchor))
        coverage = sampled_coverage(source, args.target_layer, source_map, target_map)
        result = {"contract_id": DEFORMATION_CONTRACT_ID,
                  "source_map": source_map.to_mapping(), "target_map": target_map.to_mapping(),
                  "coverage": coverage.to_mapping()}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
