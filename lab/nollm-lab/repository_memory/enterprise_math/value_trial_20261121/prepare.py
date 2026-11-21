"""Prepare the development trial from an existing local source checkout."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--runtime', type=Path, required=True)
p.add_argument('--field', type=Path, required=True)
p.add_argument('--source-repo', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
root = a.out.resolve()
root.mkdir(parents=True, exist_ok=True)
manifest_path = Path(__file__).with_name('corpus-manifest.json')
manifest = json.loads(manifest_path.read_text())
source_revision = manifest['revision']
field = root / 'field'
shutil.copytree(a.field, field)
sys.path.insert(0, str(a.runtime.resolve()))
from enterprise_math.research import describe

ids = [json.loads(path.read_text())['statement']['statement_id']
       for path in (field / 'access/statements').rglob('*.json')]
flat = [describe(field, note_id) for note_id in sorted(ids)]
(root / 'flat.json').write_text(json.dumps(flat, ensure_ascii=False, indent=2) + '\n')
for entry in manifest['files']:
    content = subprocess.check_output(['git', '-C', str(a.source_repo), 'show', f"{source_revision}:{entry['path']}"])
    target = root / 'corpus' / entry['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
(root / 'corpus-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
config = {'runtime': str(a.runtime.resolve()), 'field': str(field),
          'corpus': str(root / 'corpus'), 'flat': str(root / 'flat.json'),
          'manifest': str(root / 'corpus-manifest.json'),
          'source_revision': source_revision,
          'nollm_revision': 'ddf7dc00b2cea43dccc5d783d20aa88e21de4e0b'}
(root / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
print(root / 'config.json')
