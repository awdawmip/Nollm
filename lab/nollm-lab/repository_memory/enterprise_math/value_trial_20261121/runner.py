"""Small trusted-input development trial; native memory is unchanged and read-only."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--arm', choices=['N', 'F', 'S'], required=True)
    p.add_argument('--case', required=True)
    p.add_argument('--log', type=Path, required=True)
    ops = p.add_subparsers(dest='op', required=True)
    ops.add_parser('catalogue')
    find = ops.add_parser('find')
    find.add_argument('term')
    find.add_argument('--limit', type=int, default=20)
    show = ops.add_parser('show')
    show.add_argument('id')
    read = ops.add_parser('read')
    read.add_argument('path')
    read.add_argument('first', type=int)
    read.add_argument('last', type=int)
    source = ops.add_parser('source')
    source.add_argument('reference')
    walk = ops.add_parser('walk')
    walk.add_argument('choices', nargs='*')
    walk.add_argument('--order', type=int)
    walk.add_argument('--page-size', type=int, default=3)
    walk.add_argument('--steps', type=int, default=1)
    walk.add_argument('--limit', type=int, default=5)
    walk.add_argument('--via', choices=['local', 'vertical'], default='local')
    a = p.parse_args()
    config = json.loads(a.config.read_text())
    sys.path.insert(0, config['runtime'])
    from enterprise_math.research import describe, walk as native_walk
    field = Path(config['field'])
    corpus = Path(config['corpus'])
    flat = json.loads(Path(config['flat']).read_text())
    files = json.loads(Path(config['manifest']).read_text())['files']

    def excerpt(path, first, last):
        lines = (corpus / path).read_text().splitlines()
        return {'reference': f"{config['source_revision']}:{path}#L{first}-L{last}",
                'text': '\n'.join(f'{i}\t{lines[i-1]}' for i in range(first, last+1))}

    started = time.perf_counter()
    at = datetime.now(timezone.utc).isoformat()
    if a.op == 'walk':
        result = native_walk(field, a.choices, a.order, a.page_size, a.steps, a.limit, a.via)
    elif a.op == 'catalogue':
        if a.arm == 'S':
            result = [{'path': f['path'], 'title': (corpus/f['path']).read_text().splitlines()[0],
                       'lines': len((corpus/f['path']).read_text().splitlines())} for f in files]
        else:
            result = [{'id': n['id'], 'preview': n['text'].splitlines()[0]} for n in flat if n['current']]
    elif a.op == 'find':
        term = a.term.casefold()
        if a.arm == 'S':
            result = [{'path': f['path'], 'line': i, 'text': line}
                      for f in files for i, line in enumerate((corpus/f['path']).read_text().splitlines(), 1)
                      if term in line.casefold()][:a.limit]
        else:
            result = [{'id': n['id'], 'preview': n['text'].splitlines()[0]}
                      for n in flat if n['current'] and (term in n['id'].casefold() or term in n['text'].casefold())][:a.limit]
    elif a.op == 'show':
        result = describe(field, a.id)
    elif a.op == 'read':
        result = excerpt(a.path, a.first, a.last)
    elif a.op == 'source':
        blob, span = a.reference.rsplit('#L', 1)
        _, path = blob.split(':', 1)
        first, _, last = span.partition('-L')
        result = excerpt(path, int(first), int(last or first))
    out = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    elapsed = time.perf_counter() - started
    record = {'at': at, 'arm': a.arm, 'case': a.case, 'op': a.op,
              'argv': sys.argv[1:], 'seconds': elapsed,
              'stdout_utf8_bytes': len(out.encode()), 'stdout': out}
    a.log.parent.mkdir(parents=True, exist_ok=True)
    with a.log.open('a') as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(out, end='')


if __name__ == '__main__':
    main()
