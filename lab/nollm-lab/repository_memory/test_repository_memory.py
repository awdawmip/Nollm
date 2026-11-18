"""Regression checks on real local Git commits and a temporary native field."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

from repo_notes import capture, inspect_notes, inventory, main
from contextlib import redirect_stdout
from io import StringIO


class RepositoryMemoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name, "source")
        self.repo.mkdir()
        self.manifest = Path(self.temp.name, "notes.json")
        self.git("init", "-q")
        for path, value in {"public.py": "API = 1", "schema[x].json": "[1]", "snapshot.py": "PORT = 1"}.items():
            (self.repo / path).write_text(value)
        self.first = self.commit()
        self.authored = {"reviewed_commit": self.first, "notes": [
            {"key": "api", "text": "The API relies on the tracked schema.", "source": "public.py", "also": ["schema[x].json"]},
            {"key": "snap", "text": "The snapshot takes port bytes.", "source": "snapshot.py"},
        ]}
        self.notes = capture(self.repo, self.manifest, self.authored)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True).strip()

    def commit(self):
        self.git("add", "-A")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "-c",
                 "commit.gpgSign=false", "commit", "-qm", "test snapshot")
        return self.git("rev-parse", "HEAD")

    def test_support_change_is_selective_and_review_is_pinned(self):
        before = self.manifest.read_bytes()
        (self.repo / "schema[x].json").write_text("[2]")
        self.assertEqual(inspect_notes(self.repo, self.notes)["notes"][0]["status"], "current")
        second = self.commit()
        statuses = {n["key"]: n["status"] for n in inspect_notes(self.repo, self.notes)["notes"]}
        self.assertEqual(statuses, {"api": "stale", "snap": "current"})
        with self.assertRaises(ValueError):
            capture(self.repo, self.manifest, self.authored)
        self.assertEqual(self.manifest.read_bytes(), before)
        view = StringIO()
        with redirect_stdout(view):
            main(["view", "--repo", str(self.repo), "--manifest", str(self.manifest)])
        self.assertIn("The snapshot takes port bytes.", view.getvalue())
        self.assertNotIn("The API relies", view.getvalue())
        updated = capture(self.repo, self.manifest, {"reviewed_commit": second, "notes": [{
            **self.authored["notes"][0], "text": "The API now relies on schema version two."}]})
        original = next(n for n in self.notes["notes"] if n["key"] == "snap")
        self.assertIn(original, updated["notes"])
        self.assertTrue(all(n["status"] == "current" for n in inspect_notes(self.repo, updated)["notes"]))

    def test_renamed_evidence_requires_review_and_bad_batch_is_not_written(self):
        (self.repo / "schema[x].json").rename(self.repo / "schema-new.json")
        second = self.commit()
        missing = inspect_notes(self.repo, self.notes)["notes"][0]
        self.assertEqual((missing["status"], missing["changes"][0]["path"]), ("deleted", "schema[x].json"))
        before = self.manifest.read_bytes()
        with self.assertRaises(ValueError):
            capture(self.repo, self.manifest, {"reviewed_commit": second, "notes": [
                {"key": "ok", "text": "A valid first note.", "source": "public.py"},
                {"key": "bad", "text": "A file that is not present.", "source": "absent.py"}]})
        self.assertEqual(self.manifest.read_bytes(), before)
        self.assertTrue(all(n["status"] == "current" for n in inspect_notes(self.repo, self.notes, self.first)["notes"]))

    def test_native_field_reopens_and_only_reaches_nearby_notes(self):
        from field_demo import run_field_demo

        authored = {"reviewed_commit": self.first, "notes": [
            {"key": "near", "text": "A related note about the API.", "source": "public.py"}]}
        three = capture(self.repo, self.manifest, authored)
        result = run_field_demo(self.repo, three,
                                [("api", 0, 0), ("near", 1, 0), ("snap", 8, 0)], (0, 0))
        recalled = {r["statement_id"].split("@")[0]: r for r in result["recalled"]}
        self.assertEqual(set(recalled), {"api", "near"})
        self.assertIn("lateral", recalled["near"]["kernel_path"])
        self.assertEqual(recalled["api"]["source"], f"{self.first}:public.py")
        self.assertEqual(len(recalled["api"]["evidence_blobs"]), 2)
        (self.repo / "schema[x].json").unlink()
        self.commit()
        with self.assertRaisesRegex(ValueError, "deleted"):
            run_field_demo(self.repo, three, [("api", 0, 0)], (0, 0))

    def test_review_queue_shows_changed_evidence_and_hides_old_judgment(self):
        (self.repo / "schema[x].json").unlink()
        target = self.commit()
        command = ["review", "--repo", str(self.repo), "--manifest", str(self.manifest)]
        output = StringIO()
        with redirect_stdout(output):
            main(command)
        queue = json.loads(output.getvalue())
        self.assertEqual(queue["commit"], target)
        self.assertEqual([n["key"] for n in queue["notes"]], ["api"])
        item = queue["notes"][0]
        self.assertNotIn("text", item)
        self.assertEqual(item["reviewed_commit"], self.first)
        self.assertEqual(item["changes"][0]["path"], "schema[x].json")
        historical = StringIO()
        with redirect_stdout(historical):
            main([*command, "--rev", self.first])
        self.assertEqual(json.loads(historical.getvalue())["notes"], [])

    def test_scope_inventory_and_exact_evidence_output(self):
        scope = inventory(self.repo, ["."], self.notes)
        self.assertEqual(scope["counts"], {"primary": 2, "support": 1, "unrecorded": 0})
        source = [sys.executable, str(Path(__file__).with_name("repo_notes.py")), "source",
                  "--repo", str(self.repo), "--manifest", str(self.manifest), "--key", "api"]
        self.assertEqual(subprocess.check_output(source + ["--evidence-index", "1"]), b"[1]")
        (self.repo / "new.py").write_text("NEW = 1")
        (self.repo / "schema[x].json").write_text("[2]")
        self.commit()
        self.assertEqual(inventory(self.repo, ["."], self.notes)["counts"]["unrecorded"], 1)
        view = inventory(self.repo, ["public.py"], self.notes)
        self.assertEqual([n["key"] for n in view["review"]], ["api"])
        changed = subprocess.run(source, capture_output=True)
        self.assertEqual((changed.returncode, changed.stdout), (2, b""))
        self.assertIn(b"stale", changed.stderr)
        self.assertEqual(subprocess.check_output(source + ["--rev", self.first]), b"API = 1")


if __name__ == "__main__":
    unittest.main()
