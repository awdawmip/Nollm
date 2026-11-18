"""Measure wall time to prepare an initial reading packet, excluding agent activity."""
import argparse
import json
from pathlib import Path
from statistics import median
from time import perf_counter_ns

from compare import ARMS, TASKS, packet


def measure(repo, repeats):
    samples = {arm: [] for arm in ARMS}
    for rep in range(repeats):
        # Rotate the start arm. Each memory invocation is a fresh subprocess and field.
        order = ARMS[rep % len(ARMS):] + ARMS[:rep % len(ARMS)]
        for task in TASKS:
            for arm in order:
                start = perf_counter_ns()
                packet(repo, task, arm)
                samples[arm].append((perf_counter_ns() - start) / 1_000_000)
    return {arm: {"samples_ms": times, "median_ms": median(times)} for arm, times in samples.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=Path("."), type=Path)
    parser.add_argument("--repeats", default=4, type=int, help="rounds across all three tasks")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    print(json.dumps(measure(args.repo.resolve(), args.repeats), indent=2))
