"""Repeat the published known-cell selector. Count actual renders including failed attempts."""
import argparse
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import perf_counter
from unittest.mock import patch


def size(value):
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode())


def populate(field, count):
    from enterprise_math.research import save_statement
    radius = 0
    points = []
    while len(points) < count:
        radius += 1
        points = [(q, r) for q in range(-radius, radius + 1) for r in range(-radius, radius + 1)
                  if max(abs(q), abs(r), abs(q+r)) <= radius]
    points = sorted(points, key=lambda qr: (max(abs(qr[0]), abs(qr[1]), abs(sum(qr))), qr))[:count]
    for i, cell in enumerate(points):
        body = (f"Synthetic note {i:04d}: controlled independent proposition.\n"
                f"Topic {i % 8}; variable a_{i:04d}; this note records cell {cell}.\n"
                "Its purpose is I/O and navigation measurement. It has no scientific evidential status.")
        save_statement(field, f"synthetic-{i:04d}", body, [f"synthetic-source:{i:04d}"], cell, None)
    return points


def memberships(field):
    from enterprise_math.research import SCOPE
    from nollm_core import CoreRuntime
    result = {}
    with CoreRuntime(field) as core:
        for order in range(9):
            after = None
            while True:
                page = core.surface_page(SCOPE, order, after, 256)
                for p in page.cells:
                    result[order, p.address.q, p.address.r] = {(c.layer, c.q, c.r) for c in p.source_cells}
                if not page.has_more:
                    break
                after = page.next_after
    return result


def trial(field, membership, i, cell, order, width, incremental):
    from enterprise_math.research import walk
    from nollm_access import AccessSurfaceNavigator
    target = (0, *cell)
    row = dict(index=i, order=order, width=width, incremental=incremental, choices=[], calls=0,
               renders=0, input_bytes=0, output_bytes=0, cursor_in_bytes=0, cursor_out_bytes=0, host_output_bytes=0,
               elapsed_ms=0, reached=False)
    cursor = None

    def counted(original):
        def render(*args):
            page = original(*args)
            row['renders'] += 1
            return page
        return render

    with patch.object(AccessSurfaceNavigator, 'page', counted(AccessSurfaceNavigator.page)), \
         patch.object(AccessSurfaceNavigator, '_physical_entry_page', counted(AccessSurfaceNavigator._physical_entry_page)):
        while True:
            choices = row['choices'][-1:] if incremental else row['choices']
            request = dict(choices=choices, order=order, page_size=width, steps=1, limit=5, via='local')
            if incremental:
                request.update(cursor=cursor, with_cursor=True)
            row['calls'] += 1
            row['input_bytes'] += size(request)
            row['cursor_in_bytes'] += size(cursor) if cursor else 0
            at = perf_counter()
            try:
                page = walk(field, **request)
            except (RuntimeError, ValueError) as error:
                row['failure'] = str(error)
                break
            finally:
                row['elapsed_ms'] += (perf_counter() - at) * 1000
            row['output_bytes'] += size(page)
            cursor = page.pop('cursor', None)
            row['cursor_out_bytes'] += size(cursor) if cursor else 0
            row['host_output_bytes'] += size(page)
            if 'start' in page:
                row['start'] = page['start']
                row['used_width'] = page['page_size']
            row['pages'] = page['surface_calls']
            if page['kind'] == 'entry':
                row['entry'] = page['entry']
                row['items'] = [h['id'] for h in page['items']]
                row['reached'] = tuple(page['entry']) == target and f'synthetic-{i:04d}' in row['items']
                break
            if page['kind'] == 'physical':
                match = next((c for c in page['candidates'] if tuple(c['physical_cell']) == target), None)
            else:
                match = next((c for c in page['candidates'] if target in membership[tuple(c['window'])]), None)
            if not match and not page['has_more']:
                row['failure'] = 'no matching descent'
                break
            row['choices'].append(match['id'] if match else 'next')
    row['elapsed_ms'] = round(row['elapsed_ms'], 1)
    return row


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runtime', type=Path)
    parser.add_argument('count', type=int)
    parser.add_argument('out', type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.runtime))
    with TemporaryDirectory() as tmp:
        field = Path(tmp) / 'field'
        at = perf_counter()
        points = populate(field, args.count)
        results = {'size': args.count, 'build_ms': round((perf_counter()-at)*1000, 1), 'trials': []}
        at = perf_counter()
        membership = memberships(field)
        results['oracle_ms'] = round((perf_counter()-at)*1000, 1)
        targets = [0] if args.count == 512 else [0, args.count//2, args.count-1]
        for order, width, incremental in [(None,3,True), (None,None,True), (None,8,True),
                                          (0,8,True), (4,8,True), (None,3,False)]:
            for i in targets:
                if not incremental and i != 0:
                    continue
                row = trial(field, membership, i, points[i], order, width, incremental)
                results['trials'].append(row)
                args.out.write_text(json.dumps(results, indent=2) + '\n')
                print(args.count,i,order,width,incremental,row['reached'],row['calls'],row['renders'],row['elapsed_ms'],flush=True)
