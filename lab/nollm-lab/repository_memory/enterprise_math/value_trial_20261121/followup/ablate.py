"""Replay the connected reader's observed choice of the designated study entry on four copies."""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

from prepare import LINK, write


def ablate(root, runtime, reads):
    sys.path.insert(0, str(runtime))
    from enterprise_math.research import walk
    path = []
    for line in reads.read_text().splitlines():
        row = json.loads(line)
        if row['action'][0] != 'walk' or row['error']:
            continue
        choices = row['action'][1:]
        path = path + choices if choices else []
        page = json.loads(row['out'])
        if page['kind'] == 'entry' and page['items'][0]['id'] == LINK[1]:
            break
    else:
        raise ValueError("reader did not select the study entry")
    results = {}
    for arm, via in [('N','connected'),('P','connected'),('L','connected'),('L','local'),('U','connected')]:
        at = perf_counter()
        result = walk(root/arm, path, None, None, 1, 5, via)
        results[f'{arm}-{via}'] = {'ms': round((perf_counter()-at)*1000, 2), 'entry': result['entry'],
                                   'items': [(i['id'],i['via']) for i in result['items']]}
        if arm == 'N':
            unlinked = result
        if arm == 'U':
            assert result == unlinked
    return {'reader': 'L', 'choices': path, 'before_equals_revoked_full_recall': True, 'runs': results}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root','runtime','reads','out'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    write(a.out, ablate(a.root, a.runtime, a.reads))
