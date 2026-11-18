"""Automatic task routing over a real repository and reopened native field."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from repo_notes import capture
from task_recall import recall_task


class TaskRecallTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name, "repo")
        self.git = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "-c", "commit.gpgSign=false", "-C", str(self.repo)]
        self.repo.mkdir()
        subprocess.run([*self.git, "init", "-q"], check=True)
        for name in ("reader.py", "schema.json", "validation.py", "billing.py"):
            (self.repo / name).write_text(name)
        self.first = self.commit()
        self.manifest = Path(self.temp.name, "notes.json")
        self.notes = capture(self.repo, self.manifest, {
            "reviewed_commit": self.first, "notes": [
                {"key": "reader@v1", "source": "reader.py", "also": ["schema.json"],
                 "text": "The structured reader obtains fields from SchemaRegistry."},
                {"key": "validator", "source": "validation.py", "also": ["schema.json"],
                 "text": "Required fields are checked against the shared schema."},
                {"key": "billing", "source": "billing.py", "text": "订单计费使用整数。"},
            ]})

    def commit(self):
        subprocess.run([*self.git, "add", "-A"], check=True)
        subprocess.run([*self.git, "commit", "-qm", "fixture"], check=True)
        return subprocess.check_output([*self.git, "rev-parse", "HEAD"], text=True).strip()

    def test_native_neighbors_order_bound_and_citations(self):
        result = recall_task(self.repo, self.notes, "Registry")
        self.assertEqual(result["entry_key"], "reader@v1")
        self.assertEqual(result["matched_terms"], ["registry"])
        self.assertEqual([n["key"] for n in result["matches"]], ["reader@v1", "validator"])
        self.assertEqual([n["kernel_path"] for n in result["matches"]], [[], ["lateral"]])
        for item in result["matches"]:
            original = next(n for n in self.notes["notes"] if n["key"] == item["key"])
            for name in ("text", "reviewed_commit", "evidence"):
                self.assertEqual(item[name], original[name])
        reverse = {**self.notes, "notes": list(reversed(self.notes["notes"]))}
        self.assertEqual(recall_task(self.repo, reverse, "Registry"), result)
        self.assertEqual(recall_task(self.repo, reverse, "Registry", limit=1)["matches"],
                         result["matches"][:1])

    def test_tie_break_is_stable_and_miss_leaks_no_bodies(self):
        # Both have one path term 'schema' with equal weight.
        self.assertEqual(recall_task(self.repo, self.notes, "schema")["entry_key"], "reader@v1")
        for query in ("what is the", "transistor"):
            result = recall_task(self.repo, self.notes, query)
            self.assertEqual(result["status"], "no_match")
            self.assertIsNone(result["entry_key"])
            self.assertEqual(result["matches"], [])
        for limit in (True, 0, 8):
            with self.assertRaisesRegex(ValueError, "limit"):
                recall_task(self.repo, self.notes, "reader", limit=limit)
        with self.assertRaisesRegex(ValueError, "query"):
            recall_task(self.repo, self.notes, "  ")

    def test_changed_support_is_removed_from_entry_and_neighborhood(self):
        # Removing only the reader's primary source leaves the validator current.
        (self.repo / "reader.py").unlink()
        self.commit()
        result = recall_task(self.repo, self.notes, "validator")
        self.assertEqual([n["key"] for n in result["matches"]], ["validator"])
        self.assertEqual(recall_task(self.repo, self.notes, "Registry")["status"], "no_match")
        (self.repo / "schema.json").write_text("{}")
        second = self.commit()
        result = recall_task(self.repo, self.notes, "validator")
        self.assertEqual((result["commit"], result["status"]), (second, "no_match"))
        old = recall_task(self.repo, self.notes, "Registry", self.first)
        self.assertEqual(len(old["matches"]), 2)
        self.assertEqual(old["commit"], self.first)

    def test_cli_han_substrings_and_stale_sources(self):
        script = Path(__file__).with_name("task_recall.py")
        command = [sys.executable, str(script), "--repo", str(self.repo),
                   "--manifest", str(self.manifest), "--query", "如何计费"]
        result = json.loads(subprocess.check_output(command))
        self.assertEqual((result["status"], result["entry_key"]), ("ok", "billing"))
        self.assertEqual(len(result["matches"]), 1)
        match = result["matches"][0]
        blob = match["evidence"][0]["blob"][:12]
        view = subprocess.check_output([*command, "--format", "view"]).decode()
        self.assertEqual(view, f"billing: 订单计费使用整数。\n  billing.py@{blob}\n")
        self.assertLess(len(view.encode()), len(json.dumps(result).encode()))
        (self.repo / "billing.py").write_text("v2")
        self.commit()
        self.assertEqual(json.loads(subprocess.check_output(command))["matches"], [])
        self.assertEqual(subprocess.check_output([*command, "--format", "view"]), b"no_match\n")


if __name__ == "__main__":
    unittest.main()
