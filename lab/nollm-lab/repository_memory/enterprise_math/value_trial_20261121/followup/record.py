"""Retain the observed actions and sizes. Git source windows can be expanded again at the saved pin."""
import argparse
from datetime import datetime
import json
from pathlib import Path
from shutil import copyfile

from prepare import write


def record(root, out, arms):
    (out/'reads').mkdir(exist_ok=True)
    (out/'answers').mkdir(exist_ok=True)
    result = {}
    for arm in arms:
        rows = [json.loads(line) for line in (root/f'{arm}.jsonl').read_text().splitlines()]
        answer = root/f'{arm}-answer.md'
        copyfile(answer, out/'answers'/f'{arm}.md')
        first = datetime.fromisoformat(rows[0]['at']).timestamp()
        last = datetime.fromisoformat(rows[-1]['at']).timestamp() + rows[-1]['ms']/1000
        totals = {'ok':0, 'failed':0, 'result_bytes':0, 'error_bytes':0, 'source_bytes':0,
                  'source_calls':0, 'action_bytes':0, 'operation_ms':0, 'entry_count':0,
                  'answer_bytes':answer.stat().st_size, 'first_to_last_s':round(last-first,2),
                  'first_to_answer_s':round(answer.stat().st_mtime-first,2)}
        with (out/'reads'/f'{arm}.jsonl').open('w') as trace:
            for row in rows:
                op = row['action'][0]
                data = row['out']
                row['out_bytes'] = len(data.encode())
                totals['action_bytes'] += len(json.dumps(row['action'], ensure_ascii=False,separators=(',',':')).encode())
                totals['operation_ms'] += row['ms']
                totals['failed' if row['error'] else 'ok'] += 1
                totals['error_bytes' if row['error'] else 'result_bytes'] += row['out_bytes']
                if op in ('source','read') and not row['error']:
                    row['reference'] = data.splitlines()[0]
                    del row['out']
                    totals['source_bytes'] += row['out_bytes']
                    totals['source_calls'] += 1
                if op == 'walk' and not row['error'] and json.loads(data)['kind'] == 'entry':
                    totals['entry_count'] += 1
                trace.write(json.dumps(row,ensure_ascii=False)+'\n')
        totals['operation_ms'] = round(totals['operation_ms'],2)
        result[arm] = totals
    write(out/'costs.json',result)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path)
    p.add_argument('out',type=Path)
    p.add_argument('arms',nargs='+')
    a = p.parse_args()
    record(a.root,a.out,a.arms)
