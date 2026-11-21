"""Reader entry for this development question. Every invocation opens the same fixed sources or field."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

from prepare import PIN


def run(a):
    args = a.action
    op, *params = args
    arm, root = a.arm, a.root
    if arm in ('N', 'P', 'L', 'U'):
        cli = [sys.executable, '-I', str(a.skill/'scripts/memory.py'), 'em', '--field', str(root/arm)]
        if op == 'walk':
            cli += ['walk', '--cursor-file', str(root/(arm+'.cursor')), '--via', 'connected', *params]
        elif op == 'show':
            cli += ['show', *params]
        elif op == 'source':
            cli += ['source', '--repo', str(a.repo), '--id', params[0], '--number', params[1] if len(params)>1 else '1']
        elif op != 'read':
            raise ValueError("native entry: walk, show, source, read")
        if op != 'read':
            return subprocess.check_output(cli, text=True)
    if arm == 'F':
        notes = json.loads((root/'flat.json').read_text())
        if op in ('catalogue', 'find'):
            term = params[0].casefold() if op == 'find' else ''
            return pretty([{'id': n['id'], 'preview': n['text'].splitlines()[0]} for n in notes
                           if n['current'] and (term in n['id'].casefold() or term in n['text'].casefold())])
        if op in ('show', 'source'):
            n = next(n for n in notes if n['id'] == params[0])
            if op == 'show':
                return pretty(n)
            reference = n['sources'][int(params[1]) - 1 if len(params)>1 else 0]
            blob, span = reference.rsplit('#L',1)
            path = blob.split(':',1)[1]
            first, _, last = span.partition('-L')
            return window(a.repo, path, int(first), int(last or first))
    paths = json.loads((root/'paths.json').read_text())
    if op == 'read':
        path, first, last = params
        return window(a.repo, path, int(first), int(last))
    if arm == 'S':
        if op == 'catalogue':
            return pretty([{'path': path, 'title': doc(a.repo, path)[0]} for path in paths])
        if op == 'find':
            term = params[0].casefold()
            limit = int(params[1]) if len(params)>1 else 20
            hits = ({'path': path, 'line': i, 'text': line}
                    for path in paths for i,line in enumerate(doc(a.repo,path),1) if term in line.casefold())
            from itertools import islice
            return pretty(list(islice(hits, limit)))
    raise ValueError(f"unknown {arm} operation {op}")


def pretty(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + '\n'


def doc(repo, path):
    return subprocess.check_output(['git','-C',str(repo),'show',f'{PIN}:{path}']).decode().splitlines()


def window(repo, path, first, last):
    lines = doc(repo, path)
    span = f'#L{first}' if last == first else f'#L{first}-L{last}'
    return f'{PIN}:{path}{span}\n' + ''.join(f'{i}\t{lines[i-1]}\n' for i in range(first,last+1))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True, type=Path)
    p.add_argument('--skill', required=True, type=Path)
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('arm', choices=['F','S','N','P','L','U'])
    p.add_argument('action', nargs=argparse.REMAINDER)
    a = p.parse_args()
    at = datetime.now(timezone.utc).isoformat()
    started = perf_counter()
    try:
        result = run(a)
        error = None
    except Exception as exc:  # Include failed material requests in this trial's cost.
        result = str(exc) + '\n'
        error = type(exc).__name__
    rec = {'at': at, 'arm': a.arm, 'action': a.action, 'ms': round(1000*(perf_counter()-started),3),
           'error': error, 'out': result}
    with (a.root/(a.arm+'.jsonl')).open('a') as log:
        log.write(json.dumps(rec,ensure_ascii=False)+'\n')
    print(result,end='')
    sys.exit(int(error is not None))
