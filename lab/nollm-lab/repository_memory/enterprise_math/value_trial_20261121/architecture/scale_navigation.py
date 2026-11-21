"""Local engineering diagnostic; synthetic placement is not semantic-quality evidence."""
import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time


def measured(call):
    started = time.perf_counter()
    value = call()
    return value, (time.perf_counter() - started) * 1000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--page-size", type=int, default=3)
    parser.add_argument("--targets", type=int, nargs="+")
    args = parser.parse_args()
    sys.path.insert(0, str(args.runtime))
    from enterprise_math.research import SCOPE, save_statement, walk
    from nollm_core import CoreRuntime

    result = {
        "purpose": "synthetic geometry reachability and engineering cost; no semantic-quality claim",
        "runtime": str(args.runtime),
        "nollm_revision": "ddf7dc00b2cea43dccc5d783d20aa88e21de4e0b",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "size": args.size,
        "source": "Synthetic notes generated only inside a temporary local field",
        "navigation": f"Current adapter, default order, page size {args.page_size}, steps 1, limit 5, via local",
        "page_size": args.page_size,
        "selector": "Greedy geometry-membership oracle: first shown candidate containing the known target; not an optimal-path oracle, LLM, or semantic router",
        "measurement": "Wall-clock milliseconds; repeated in-process calls may benefit from disposable kernel caches; CLI probes use a fresh process each time",
    }

    def checkpoint():
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    # Compact hexagonal spiral ordering: one independent statement per layer-zero cell.
    radius = 0
    points = []
    while len(points) < args.size:
        radius += 1
        points = [(q, r) for q in range(-radius, radius + 1)
                  for r in range(-radius, radius + 1)
                  if max(abs(q), abs(r), abs(q+r)) <= radius]
    points.sort(key=lambda qr: (max(abs(qr[0]), abs(qr[1]), abs(sum(qr))), qr))
    points = points[:args.size]
    with tempfile.TemporaryDirectory(prefix="nollm-value-scale-") as temporary:
        field = Path(temporary) / "field"
        writes = []
        for i, cell in enumerate(points):
            text = (f"Synthetic note {i:04d}: controlled independent proposition.\n"
                    f"Topic {i % 8}; variable a_{i:04d}; this note records cell {cell}.\n"
                    "Its purpose is I/O and navigation measurement. It has no scientific evidential status.")
            _, elapsed = measured(lambda: save_statement(
                field, f"synthetic-{i:04d}", text,
                [f"synthetic-source:{i:04d}"], cell, None))
            writes.append(elapsed)
        result["build"] = {
            "total_ms": sum(writes),
            "write_median_ms": statistics.median(writes),
            "last_16_write_median_ms": statistics.median(writes[-16:]),
            "canonical_core_bytes": (field / "core/current_state.json").stat().st_size,
            "all_file_bytes": sum(p.stat().st_size for p in field.rglob("*") if p.is_file()),
            "all_file_count": sum(p.is_file() for p in field.rglob("*")),
        }
        checkpoint()
        print(json.dumps({"size": args.size, "phase": "built", **result["build"]}), flush=True)

        opens = []
        for _ in range(5):
            start = time.perf_counter()
            with CoreRuntime(field) as core:
                count = len(core.occupied_cells())
            opens.append((time.perf_counter() - start) * 1000)
        result["reopen"] = {"samples_ms": opens, "median_ms": statistics.median(opens), "occupied_cells": count}

        env = dict(os.environ, PYTHONPATH=str(args.runtime))
        cli_samples = []
        for _ in range(3):
            response, elapsed = measured(lambda: subprocess.run(
                [sys.executable, str(args.runtime / "enterprise_math/research.py"),
                 "--field", str(field), "walk", "--page-size", str(args.page_size)], env=env, text=True, capture_output=True, check=True))
            page = json.loads(response.stdout)
            cli_samples.append({"ms": elapsed, "stdout_bytes": len(response.stdout.encode()),
                                "order": page["order"], "candidate_count": len(page["candidates"]),
                                "has_more": page["has_more"],
                                "truncated_candidates": sum(c["truncated"] for c in page["candidates"])})
        result["fresh_process_root_walk"] = cli_samples
        checkpoint()
        print(json.dumps({"size": args.size, "phase": "root_walk", "samples": cli_samples}), flush=True)

        # Offline membership oracle is used ONLY to assess whether geometry can reach known cells.
        # Its construction is separately timed and excluded from adapter navigation latency.
        membership = {}
        counts = []
        start = time.perf_counter()
        with CoreRuntime(field) as core:
            for order in range(9):
                after = None
                count = 0
                while True:
                    raw = core.surface_page(SCOPE, order, after, 256)
                    for projection in raw.cells:
                        membership[(order, projection.address.q, projection.address.r)] = {
                            (cell.layer, cell.q, cell.r) for cell in projection.source_cells}
                    count += len(raw.cells)
                    if not raw.has_more:
                        break
                    after = raw.next_after
                counts.append(count)
        result["oracle_build_ms"] = (time.perf_counter() - start) * 1000
        result["surface_occupied_counts_order_0_to_8"] = counts
        result["navigation_trials"] = []
        checkpoint()

        for target_index in args.targets or (0, args.size // 2, args.size - 1):
            target = (0, *points[target_index])
            target_id = f"synthetic-{target_index:04d}"
            choices = []
            calls = []
            reached = False
            failure = None
            for _ in range(25):
                try:
                    page, elapsed = measured(lambda: walk(field, choices, None, args.page_size, 1, 5, "local"))
                except (RuntimeError, ValueError) as error:
                    failure = f"{type(error).__name__}: {error}"
                    break
                calls.append({"ms": elapsed, "output_bytes": len(json.dumps(page, ensure_ascii=False).encode()),
                              "kind": page["kind"], "order": page.get("order"),
                              "surface_calls": page["surface_calls"]})
                if page["kind"] == "entry":
                    reached = tuple(page["entry"]) == target and target_id in [i["id"] for i in page["items"]]
                    break
                if page["kind"] == "physical":
                    selected = next((c for c in page["candidates"] if tuple(c["physical_cell"]) == target), None)
                else:
                    selected = next((c for c in page["candidates"] if target in membership[tuple(c["window"])]), None)
                if selected is not None:
                    choices.append(selected["id"])
                elif page["has_more"]:
                    choices.append("next")
                else:
                    failure = "target not present on selected geometric descent"
                    break
            trial = {"target_id": target_id, "target_cell": target, "reached_and_recalled": reached,
                     "failure": failure, "api_calls": len(calls), "replayed_surface_calls": sum(c["surface_calls"] for c in calls),
                     "total_ms": sum(c["ms"] for c in calls), "output_bytes": sum(c["output_bytes"] for c in calls),
                     "choices": choices, "calls": calls}
            result["navigation_trials"].append(trial)
            checkpoint()
            print(json.dumps({"size": args.size, "phase": "navigation", **{k:v for k,v in trial.items() if k not in ("choices", "calls")}}), flush=True)
        result["temporary_field_deleted_on_exit"] = True
        checkpoint()


if __name__ == "__main__":
    main()
