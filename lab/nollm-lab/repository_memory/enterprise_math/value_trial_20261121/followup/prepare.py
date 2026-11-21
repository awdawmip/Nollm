"""Make new private trial fields from the published note versions; never open the working field."""
import argparse
import json
from pathlib import Path
from shutil import copytree
import sys
from time import perf_counter

HERE = Path(__file__).resolve().parent
PIN = "f16294a5a7ffa435a32b70214d881fd4450eb494"
# Three local families. The old and current probe results occupy the same slot.
LAYOUT = {
    "CRT.mass": (-1, 0), "CRT.repair": (0, 1), "NT-SUP-CRT-CARRY": (0, 0),
    "NT-DIV-RESIDUAL-CAPACITY": (-5, 2), "prime.threshold": (-5, 3),
    "X6-QUADRATIC-MODULAR.oct": (5, -1), "X6.parity-probes": (5, 0),
}
# Permute the identical occupied cells, keeping the comparison entry CRT.repair fixed.
PERMUTED = [(5,-1), (0,1), (-5,2), (0,0), (-1,0), (5,0), (-5,3)]
LINK = ("observer-lead", "CRT.repair", "X6-QUADRATIC-MODULAR.v2")


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def prepare(root, runtime):
    sys.path.insert(0, str(runtime))
    from enterprise_math.research import describe, save_statement, stitch, unstitch
    root.mkdir(parents=True, exist_ok=True)
    initial = perf_counter()
    notes = [n for n in json.loads((HERE.parent/'flat.json').read_text())
             if n['id'] in LAYOUT or n['id'] == LINK[2]]
    write(root/'flat.json', notes)
    paths = sorted({ref.split(':', 1)[1].split('#L')[0] for n in notes for ref in n['sources']})
    write(root/'paths.json', paths)
    receipt = {'flat_ms': (perf_counter()-initial)*1000, 'flat_bytes': (root/'flat.json').stat().st_size,
               'sources': paths, 'writes': []}
    for arm, places in [('N', LAYOUT), ('P', dict(zip(LAYOUT, PERMUTED)))]:
        for n in notes:
            rev = n.get('revises')
            args = (n['id'], n['text'], n['sources'], places.get(n['id']), rev)
            at = perf_counter()
            saved = save_statement(root/arm, *args)
            receipt['writes'].append({'arm': arm, **saved, 'ms': (perf_counter()-at)*1000,
                                      'argument_bytes': len(json.dumps(args, ensure_ascii=False).encode())})
        # This is the actual comparison invariant, including the old version and its sources.
        assert [describe(root/arm, n['id']) for n in notes] == notes
    for arm in ('L','U'):
        at = perf_counter()
        copytree(root/'N', root/arm)
        copy_ms = (perf_counter()-at)*1000
        at = perf_counter()
        receipt[arm] = {'link': stitch(root/arm, *LINK), 'copy_ms': copy_ms,
                        'stitch_ms': (perf_counter()-at)*1000}
    at = perf_counter()
    receipt['U']['undo'] = unstitch(root/'U', LINK[0])
    receipt['U']['undo_ms'] = (perf_counter()-at)*1000
    receipt['field_bytes'] = {a: sum(p.stat().st_size for p in (root/a).rglob('*') if p.is_file())
                              for a in ['N','P','L','U']}
    write(root/'formation.json', receipt)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('runtime', type=Path)
    args = p.parse_args()
    prepare(args.root, args.runtime)
