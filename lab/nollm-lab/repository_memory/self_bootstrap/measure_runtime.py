"""Measure reopening one unchanged field and reading its current statements."""
import argparse
import cProfile
import json
from pathlib import Path
import pstats
import statistics
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True, help='Nollm source checkout')
    parser.add_argument('--field', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=30)
    args = parser.parse_args()
    sys.path[:0] = [str(args.runtime / 'packages' / package / 'src')
                   for package in ('nollm-core', 'nollm-access')]
    from nollm_core import CoreRuntime
    from nollm_access import FileHandleStore, FileStatementStore

    def read():
        with CoreRuntime(args.field) as core:
            handles = tuple(handle for cell in core.occupied_cells()
                            for handle, _ in core.atoms_at(cell))
            bindings = FileHandleStore(args.field).bindings_for_handles(handles)
            store = FileStatementStore(args.field)
            return [store.get(binding.current_statement_id) for binding in bindings]

    profile = cProfile.Profile()
    started = time.perf_counter()
    statements = profile.runcall(read)
    first_seconds = time.perf_counter() - started
    tracked = {'_decode_state_bytes', '_decode_document', 'canonical_state_bytes', '_canonical'}
    counts = {f'{Path(filename).name}:{function}': values[1]
              for (filename, _, function), values in pstats.Stats(profile).stats.items()
              if function in tracked}
    times = []
    for _ in range(args.repeats):
        started = time.perf_counter()
        read()
        times.append(time.perf_counter() - started)
    print(json.dumps({'current_statements': len(statements), 'first_profiled_seconds': first_seconds,
                      'first_call_counts': counts, 'warm_repeats': args.repeats,
                      'warm_median_seconds': statistics.median(times),
                      'warm_min_seconds': min(times), 'warm_max_seconds': max(times)}, indent=2))


if __name__ == '__main__':
    main()
