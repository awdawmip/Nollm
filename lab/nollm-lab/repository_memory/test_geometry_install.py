"""Exercise the installed geometric codec independently of its source checkout."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import install_skill


META = """#AOCI-META-VOLUME: 1
#[Tag dictionary: code]
#A Layer: C-Code
#B Module: G-General
#C Importance: 7-high 1-low
#D Trait: K-kernel
#E Scale: L-large T-tiny
"""
VOLUME = """#AOCI-CODE-VOLUME: 1

===/<repository>/===
worker.py[C.G.7.K.L]: F:Schedules work | R:code:reader.py | A:submit | S:-
reader.py[CG1T]: F:Reads a queue | R:- | A:read | S:Retry after resume
"""


class GeometryInstallationTest(unittest.TestCase):
    def test_portable_volume_without_symbolic_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            executable = install_skill.install(root / "skill") / "scripts/memory.py"

            def run(*args, ok=True):
                proc = subprocess.run([sys.executable, "-I", str(executable), "aux", "aoci", *map(str, args)],
                                      cwd=root, capture_output=True)
                if ok:
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                else:
                    self.assertNotEqual(proc.returncode, 0, proc.stdout)
                return proc

            volume, meta, geometry = (root / name for name in ("aoci.code.txt", "aoci.meta.txt", "code.nlg"))
            volume.write_text(VOLUME, encoding="utf-8")
            meta.write_text(META, encoding="utf-8")
            run("encode", "--volume", volume, "--meta", meta, "--out", geometry)
            saved = geometry.read_bytes()
            self.assertNotIn(b"CG1T", saved)
            self.assertNotIn(b"F:Schedules work", saved)
            volume.unlink()
            source = ("--geometry", geometry, "--meta", meta)
            self.assertEqual(json.loads(run("check", *source).stdout), {"valid": 2})
            found = json.loads(run("query", *source, "--axis", "D=K", "--field", "A").stdout)
            self.assertEqual(found, {"matched": 1, "items": [{"id":"code:worker.py","value":"submit"}]})
            target = json.loads(run("query", *source, "--target", "code:reader.py", "--limit", "0").stdout)
            self.assertEqual(target, {"matched": 1, "items": []})
            high = json.loads(run("query", *source, "--min-importance", "6", "--feature-state", "present").stdout)
            self.assertEqual(high["items"], [{"id":"code:worker.py"}])
            rows = json.loads(run("decode", *source, "--format", "json").stdout)
            self.assertEqual(rows[0]["tags"]["D"], "K")
            self.assertNotIn("D", rows[1]["tags"])
            self.assertEqual(rows[1]["fields"]["S"], "Retry after resume")
            field = root / "native"
            def native(*args):
                return json.loads(subprocess.check_output(
                    [sys.executable, "-I", str(executable), "aux", "aoci-field", *map(str, args)], cwd=root))
            written = native("write", "--geometry", geometry, "--meta", meta, "--field", field)
            self.assertEqual(written["directed_bridges"], 1)
            probe = native("probe", "--id", "code:worker.py", "--meta", meta, "--field", field)
            self.assertEqual(probe["reference"]["target"], "code:reader.py")
            self.assertEqual(probe["reference"]["path"], ["bridge"])
            self.assertEqual(probe["ports"]["A"]["value"], "submit")
            native_rows = root / "native-rows.json"
            subprocess.run([sys.executable, "-I", str(executable), "aux", "aoci-field", "read",
                            "--meta", str(meta), "--field", str(field), "--out", str(native_rows)], check=True)
            self.assertEqual(json.loads(native_rows.read_bytes()), sorted(rows, key=lambda r:r["id"]))
            run("decode", *source, "--out", volume)
            second = root / "second.nlg"
            run("encode", "--volume", volume, "--meta", meta, "--out", second)
            self.assertEqual(saved, second.read_bytes())
            run("decode", *source, "--out", geometry, ok=False)
            self.assertEqual(saved, geometry.read_bytes())
            meta.write_text(META.replace("1-low", "2-other"), encoding="utf-8")
            run("decode", *source, ok=False)
            meta.write_text(META, encoding="utf-8")
            geometry.write_bytes(saved[:-1])
            run("query", *source, "--axis", "C=7", ok=False)
