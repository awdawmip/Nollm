"""Compare the EM-derived algorithms with the published pre-change source.

This is an opt-in benchmark, not a timing assertion or a CI gate. A Git checkout
reads the pinned baseline with local ``git show``; a partial checkout can supply
the same four fetched source files with --baseline-dir. No network is used.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import importlib
import json
from pathlib import Path
import platform
import random
from statistics import median
import subprocess
import sys
import time
import types


ROOT = Path(__file__).resolve().parents[3]
BASELINE_REF = "58ad03a5457a6a8c57768368f4d9a3448c7827cd"
PATHS = {
    "approximate_coverage.py": "packages/nollm-core/src/nollm_core/approximate_coverage.py",
    "motion.py": "lab/nollm-lab/geometry/motion.py",
    "deformation.py": "lab/nollm-lab/geometry/deformation.py",
    "pressure_evaluation.py": "lab/nollm-lab/geometry/pressure_evaluation.py",
}
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"),
                str(ROOT / "packages/nollm-access/src"),
                str(ROOT / "lab/nollm-lab")]

from nollm_core import GeometryAddress
from nollm_access import write_pressure
from geometry import deformation, motion, pressure_evaluation


def load_module(name, code, path):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = name.rpartition(".")[0]
    sys.modules[name] = module
    exec(compile(code, str(path), "exec"), module.__dict__)
    return module


def baselines(directory):
    source = {}
    for name, path in PATHS.items():
        source[name] = ((directory / name).read_text() if directory else
                        subprocess.check_output(
                            ["git", "show", f"{BASELINE_REF}:{path}"], cwd=ROOT, text=True))
    package = types.ModuleType("_nollm_before_em")
    package.__path__ = []
    sys.modules[package.__name__] = package
    result = {}
    result["core"] = load_module("nollm_core._before_em_coverage",
                                 source["approximate_coverage.py"], PATHS["approximate_coverage.py"])
    for name in ("deformation", "motion", "pressure_evaluation"):
        result[name] = load_module(f"_nollm_before_em.{name}", source[f"{name}.py"], PATHS[f"{name}.py"])
    return result


def cell(layer, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def digest_coverage(result):
    return tuple((m.target.layer, m.target.q, m.target.r, m.hit_count, m.weight_q16)
                 for m in result.members)


def without_work(value):
    if isinstance(value, dict):
        return {k: without_work(v) for k, v in value.items() if k != "work"}
    if isinstance(value, list):
        return [without_work(v) for v in value]
    return value


def timed_pair(before, after, repeats):
    samples = {"before_ms": [], "after_ms": []}
    for round_id in range(repeats):
        order = (("before_ms", before), ("after_ms", after))
        if round_id % 2:
            order = tuple(reversed(order))
        for name, run in order:
            start = time.perf_counter_ns()
            run()
            samples[name].append((time.perf_counter_ns() - start) / 1_000_000)
    old, new = median(samples["before_ms"]), median(samples["after_ms"])
    return {**samples, "before_median_ms": old, "after_median_ms": new,
            "before_over_after": old / new}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", type=Path)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--sources", type=int, default=2000)
    parser.add_argument("--motion-steps", type=int, default=256)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if min(args.repeats, args.sources, args.motion_steps) <= 0:
        parser.error("counts must be positive")
    old = baselines(args.baseline_dir)
    core = importlib.import_module("nollm_core.approximate_coverage")
    incoming = importlib.import_module("nollm_core.incoming_coverage")
    rng = random.Random(20261122)
    addresses = [cell(i % 31 - 15, rng.randrange(-2**27, 2**27),
                      rng.randrange(-2**27, 2**27)) for i in range(args.sources)]
    shared = [cell(i % 8, addresses[i // 8].q, addresses[i // 8].r)
              for i in range(args.sources)]
    result = {"baseline_ref": BASELINE_REF, "at_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "platform": platform.platform(),
              "repeats": args.repeats,
              "baseline_sources": PATHS,
              "input_seeds": {"coverage": 20261122, "motion": 852026},
              "scope": "fixed sampled-coverage equivalence and local execution cost; not semantic recall or exact-area accuracy",
              "cases": {}}

    def coverage_run(module, inputs, direction, cold):
        if cold:
            module.clear_approximate_coverage_cache()
        return [digest_coverage(module.expand_approximate_coverage(a, direction)) for a in inputs]

    for direction in ("coverage_up", "coverage_down"):
        for label, inputs, cold in (("cold_unique", addresses, True),
                                     ("cross_layer_phase_reuse", shared, True),
                                     ("warm_exact", addresses, False)):
            before = lambda: coverage_run(old["core"], inputs, direction, cold)
            after = lambda: coverage_run(core, inputs, direction, cold)
            assert before() == after()
            result["cases"][f"{direction}_{label}"] = {
                "requests": len(inputs), "outputs_equal": True,
                "includes": "complete coverage expansion and member materialization; cold cases include derived-cache initialization",
                **timed_pair(before, after, args.repeats),
            }

    @contextmanager
    def source_kernel(module):
        original = incoming.expand_approximate_coverage
        incoming.expand_approximate_coverage = module.expand_approximate_coverage
        try:
            yield
        finally:
            incoming.expand_approximate_coverage = original

    def units_at(address):
        return tuple((address.layer, address.q, address.r, i)
                     for i in range((3 * abs(address.q) + 5 * abs(address.r)) % 4))

    pressure_cells = addresses[:min(256, len(addresses))]

    def native_pressure(module):
        module.clear_approximate_coverage_cache()
        incoming._inverse_bounds.cache_clear()
        with source_kernel(module):
            return [write_pressure(a, units_at).to_mapping() for a in pressure_cells]

    before = lambda: native_pressure(old["core"])
    after = lambda: native_pressure(core)
    assert before() == after()
    result["cases"]["native_write_pressure_cold"] = {
        "requests": len(pressure_cells), "outputs_equal": True,
        "includes": "complete advisory pressure with deterministic current-unit callbacks; no disk I/O",
        **timed_pair(before, after, args.repeats),
    }

    scale = 1 << 40
    motion_rng = random.Random(852026)
    movements = {
        "safe": [(1, -1)] * args.motion_steps,
        "small_crossings": [(motion_rng.randrange(-scale // 128, scale // 128),
                             motion_rng.randrange(-scale // 128, scale // 128))
                            for _ in range(args.motion_steps)],
        "large_jumps": [(motion_rng.randrange(-4 * scale, 4 * scale),
                         motion_rng.randrange(-4 * scale, 4 * scale))
                        for _ in range(args.motion_steps)],
    }

    def motion_run(module, changes, direction, verify=False):
        footprint = module.TranslationFootprint.from_source(cell(0, 19, -17), direction)
        outputs = []
        calls = 0
        for change in changes:
            step = footprint.translate(change)
            footprint = step.footprint
            calls += step.round_calls
            outputs.append((footprint.center_q40, footprint.counts_q16(),
                            footprint.sample_targets() if verify else None))
        return outputs, calls

    for direction in ("coverage_up", "coverage_down"):
        for label, changes in movements.items():
            before_check, before_calls = motion_run(old["motion"], changes, direction, True)
            after_check, after_calls = motion_run(motion, changes, direction, True)
            assert before_check == after_check
            result["cases"][f"motion_{direction}_{label}"] = {
                "steps": len(changes), "outputs_equal": True,
                "before_round_calls": before_calls, "after_round_calls": after_calls,
                "includes": "initial footprint construction, all updates, centers and Q16 result materialization",
                **timed_pair(lambda: motion_run(old["motion"], changes, direction),
                             lambda: motion_run(motion, changes, direction), args.repeats),
            }

    lower = {cell(1, q, r): 1 + (q + r) % 4 for q in range(-8, 8) for r in range(-4, 4)}
    upper = {cell(0, q, r): 3 for q in range(-9, 10) for r in range(-5, 6)}
    for label, target_twist, source_twist in (("unchanged", None, None),
                                             ("local_target_twist", (0, 0, 2, .8), None),
                                             ("global_target_twist", (0, 0, 100, .8), None),
                                             ("source_frame_change", None, "frame")):
        def comparison(module, maps):
            kwargs = {"upper_layer": 0, "inventory_complete": True}
            if target_twist:
                x, y, radius, angle = target_twist
                kwargs["after_upper_map"] = maps.LayerMap.for_layer(0).with_twist(
                    maps.RadialTwist((x, y), radius, angle))
            if source_twist == "frame":
                before_frame = maps.LayerMap.for_layer(1).frame
                kwargs["after_lower_map"] = maps.LayerMap(before_frame.rotate_about((0, 0), .03))
            return module.compare_pressure(upper, lower, **kwargs)
        before = lambda: comparison(old["pressure_evaluation"], old["deformation"])
        after = lambda: comparison(pressure_evaluation, deformation)
        first, second = before(), after()
        assert first == without_work(second)
        result["cases"][f"lab_pressure_{label}"] = {
            "sources": len(lower), "outputs_equal": True, "candidate_work": second.get("work"),
            "includes": "fresh request, geometry, all allocations, pressure and complete JSON-ready report",
            **timed_pair(before, after, args.repeats),
        }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"baseline_ref": BASELINE_REF, "cases": {
        name: {key: value for key, value in case.items()
               if key in ("before_median_ms", "after_median_ms", "before_over_after", "outputs_equal", "candidate_work")}
        for name, case in result["cases"].items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
