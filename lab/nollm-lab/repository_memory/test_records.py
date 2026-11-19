from copy import deepcopy
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from records import compile_records, sha, write_template


class CompileRecords(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "fixture")
        self.git("config", "user.email", "fixture@example.test")
        package = self.repo / "pkg"
        package.mkdir()
        (package / "__init__.py").write_text("")
        (package / "api.py").write_text("from . import model\nclass Reader:\n    def read(self): return 3\n")
        (package / "model.py").write_text("class Model: pass\n")
        self.git("add", ".")
        self.git("commit", "-qm", "baseline")
        self.pin = self.git("rev-parse", "HEAD")
        self.out = self.repo.parent / "records.jsonl"
        evidence = [{"path":p, "blob":self.git("rev-parse", self.pin+":"+p)} for p in ["pkg/api.py","pkg/model.py"]]
        self.group = dict(key="tree.pkg",text="module group",reviewed_commit=self.pin,evidence=evidence)
        self.imports = dict(key="imports.pkg",text="pkg.api 第 1 行导入 pkg.model",reviewed_commit=self.pin,evidence=evidence)
        self.review = dict(key="api.read",text="The reader accepts samples.",reviewed_commit=self.pin,evidence=evidence)
        self.manifest = dict(schema="nollm_repo_notes_v1",notes=[self.review, self.group, self.imports])
        self.claims = {"api.read":dict(legacy_sha256=sha(self.review), atoms=[["Reader.read","accepts","sample"]])}

    def git(self,*args):
        return subprocess.check_output(["git","-C",str(self.repo),*args]).decode().strip()

    def write(self,manifest=None,claims=None,imports=None):
        compile_records(self.repo, "HEAD", self.manifest if manifest is None else manifest,
                        self.claims if claims is None else claims, imports or {}, self.out)
        return {r["key"]:r for r in map(json.loads,self.out.read_bytes().splitlines())}

    def test_all_types_pinned_and_spelling_verified(self):
        rows = self.write()
        self.assertEqual(rows["api.read"]["symbol_anchors"],[{"symbol":"Reader.read","line":3,"path":"pkg/api.py"}])
        self.assertEqual(rows["imports.pkg"]["import_sites"],[{"source":"pkg/api.py","target":"pkg/model.py","line":1}])
        self.assertEqual(rows["tree.pkg"]["type_counts"],{"py":2})
        self.assertNotIn(self.review["text"].encode(),self.out.read_bytes())
        self.assertEqual(rows["api.read"]["legacy_sha256"],sha(self.review))
        first = self.out.read_bytes()
        self.manifest["notes"].reverse()
        self.write()
        self.assertEqual(first,self.out.read_bytes())

    def test_new_snapshot_reuses_unchanged_evidence_and_rejects_changed_support(self):
        (self.repo/"unrelated").write_text("another file\n")
        self.git("add",".")
        self.git("commit","-qm","unrelated")
        rows = self.write()
        for row in rows.values():
            self.assertEqual(row["commit"],self.git("rev-parse","HEAD"))
            self.assertEqual(row["reviewed_commit"],self.pin)
        first = self.out.read_bytes()
        (self.repo/"pkg/model.py").write_text("class Updated: pass\n")
        self.git("add",".")
        self.git("commit","-qm","changed support")
        with self.assertRaisesRegex(ValueError,"stale"):
            self.write()
        self.assertEqual(first,self.out.read_bytes())

    def test_forged_import_location_does_not_become_a_static_fact(self):
        changed = deepcopy(self.imports)
        changed["text"] = changed["text"].replace("1","2")
        with self.assertRaisesRegex(ValueError,"no matching static import"):
            self.write(dict(schema="nollm_repo_notes_v1",notes=[changed]),claims={})
        opaque = dict(self.imports,text="import graph")
        rows = self.write(dict(schema="nollm_repo_notes_v1",notes=[opaque]),claims={},
                          imports={"imports.pkg":[dict(source_module="pkg.api",target_module="pkg.model",line=1)]})
        self.assertEqual(rows["imports.pkg"]["atoms"],[["pkg.api","imports","pkg.model"]])

    def test_authored_projection_cannot_silently_follow_replaced_legacy_text(self):
        old = deepcopy(self.manifest)
        old["notes"][0]["text"] = "a different interpretation"
        with self.assertRaisesRegex(ValueError,"does not bind"):
            self.write(old)
        with self.assertRaisesRegex(ValueError,"claim keys differ"):
            self.write(claims={})

    def test_template_generates_exact_claim_keys_and_preserves_existing_edit(self):
        path = self.repo.parent / "mapping.json"
        self.assertEqual(write_template(self.manifest,path),1)
        expected = {"api.read":{"atoms":[],"legacy_sha256":sha(self.review)}}
        self.assertEqual(json.loads(path.read_bytes()),expected)
        path.write_text("my draft")
        with self.assertRaises(FileExistsError):
            write_template(self.manifest,path)
        self.assertEqual(path.read_text(),"my draft")

    def test_repeated_keys_and_paths_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate or empty note key"):
            self.write(dict(schema="nollm_repo_notes_v1",notes=[self.review,self.review]))
        duplicate = deepcopy(self.group)
        duplicate["evidence"].append(duplicate["evidence"][0])
        with self.assertRaisesRegex(ValueError,"duplicated evidence"):
            self.write(dict(schema="nollm_repo_notes_v1",notes=[duplicate]),claims={})

    def test_imported_attribute_is_not_automatically_a_resolved_submodule(self):
        # No evidence file matches the claimed target and the import is not guessed.
        changed = dict(self.imports,text="pkg.api 第 1 行导入 pkg.unknown")
        with self.assertRaisesRegex(ValueError,"0 matching evidence paths"):
            self.write(dict(schema="nollm_repo_notes_v1",notes=[changed]),claims={})


if __name__ == "__main__":
    unittest.main()
