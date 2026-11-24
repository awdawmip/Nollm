"""Real temporary fields only; no production notebook or remote writes."""
from pathlib import Path
import hashlib
import importlib
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from enterprise_math import research
from nollm_access import FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime, MemoryAtom
from coverage_cli import address


class RevisionContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.field = self.root / "field"
        self.repo = self.root / "evidence"
        self.repo.mkdir()
        self.git("init", "-q")
        self.old_source = self.commit_source("original source statement\n")
        research.save_statement(self.field, "note.v0", "original note", [self.old_source], (0, 0), None)
        self.new_source = self.commit_source("revised source statement\n")
        research.save_statement(self.field, "note.v1", "middle note", [self.new_source], None, "note.v0")
        research.save_statement(self.field, "note.v2", "current note", [self.new_source], None, "note.v1")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True).strip()

    def commit_source(self, text):
        (self.repo / "statement.md").write_text(text)
        self.git("add", "statement.md")
        self.git("-c", "user.name=Local Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-qm", "fixture source")
        return f"{self.git('rev-parse', 'HEAD')}:statement.md#L1"

    def field_bytes(self):
        return {str(path.relative_to(self.field)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.field.rglob("*") if path.is_file()}

    def add_physical_candidate(self, note_id, text, refs, cell, atom_id="note.v0"):
        statement = MemoryStatement(note_id, text, self.new_source, tuple(refs))
        FileStatementStore(self.field).put(statement)
        with CoreRuntime(self.field) as core:
            handle = core.put(MemoryAtom(atom_id, text), address(0, *cell))
        FileHandleStore(self.field).put(note_id, handle)
        return handle

    def test_old_id_keeps_text_sources_and_locates_current_without_global_body_scan(self):
        for number in range(12):
            research.save_statement(self.field, f"unrelated.{number}", "unrelated understanding",
                                    [self.new_source], (number + 10, 0), None)
        before = self.field_bytes()
        reads = []
        original = FileStatementStore.get

        def record(store, note_id):
            reads.append(note_id)
            return original(store, note_id)

        implementation = importlib.import_module(research.describe.__module__)
        with patch.object(FileStatementStore, "get", record), patch.object(implementation, "CoreRuntime", side_effect=AssertionError("show must not open Core")):
            old = research.describe(self.field, "note.v0")
        self.assertEqual(old["text"], "original note")
        self.assertEqual(old["sources"], [self.old_source])
        self.assertFalse(old["current"])
        self.assertEqual(old["continuation"], {"scope": "native_revision_slot", "status": "unique",
                                              "candidates": [{"id": "note.v2", "cell": [0, 0, 0]}]})
        self.assertEqual(set(reads), {"note.v0", "note.v1", "note.v2"})
        self.assertEqual(len(reads), 3)
        self.assertEqual(before, self.field_bytes())
        current = research.describe(self.field, old["continuation"]["candidates"][0]["id"])
        self.assertEqual(current["text"], "current note")
        self.assertTrue(current["current"])
        self.assertEqual(current["revises"], "note.v1")
        self.assertEqual(current["sources"], [self.new_source])
        self.assertNotIn("continuation", current)
        self.assertIn("original source statement", research.excerpt(self.repo, old["sources"][0]))
        self.assertIn("revised source statement", research.excerpt(self.repo, current["sources"][0]))

    def test_middle_revision_and_moved_slot_remain_locatable(self):
        bindings = FileHandleStore(self.field)
        old_handle = bindings.get("note.v2")
        with CoreRuntime(self.field) as core:
            moved = core.move(old_handle, address(0, 4, -2))
        bindings.move_handle(old_handle, moved)
        continuation = research.describe(self.field, "note.v1")["continuation"]
        self.assertEqual(continuation["status"], "unique")
        self.assertEqual(continuation["candidates"], [{"id": "note.v2", "cell": [0, 4, -2]}])

    def test_shared_local_atom_id_does_not_create_false_successor(self):
        self.add_physical_candidate("unrelated.collision", "other proposition", (), (5, 0))
        continuation = research.describe(self.field, "note.v1")["continuation"]
        self.assertEqual(continuation["status"], "unique")
        self.assertEqual([item["id"] for item in continuation["candidates"]], ["note.v2"])

    def test_native_fork_returns_both_candidates(self):
        self.add_physical_candidate("note.alternate", "alternative continuation", ("revises:note.v1",), (5, 0))
        continuation = research.describe(self.field, "note.v1")["continuation"]
        self.assertEqual(continuation["status"], "ambiguous")
        self.assertEqual({item["id"] for item in continuation["candidates"]}, {"note.v2", "note.alternate"})

    def test_removed_binding_returns_no_current_guess(self):
        bindings = FileHandleStore(self.field)
        bindings.remove_handle(bindings.get("note.v2"))
        old = research.describe(self.field, "note.v1")
        self.assertEqual(old["text"], "middle note")
        self.assertEqual(old["continuation"]["status"], "not_found")
        self.assertEqual(old["continuation"]["candidates"], [])

    def test_missing_revision_evidence_reports_incomplete(self):
        FileStatementStore(self.field)._path("note.v1").unlink()
        old = research.describe(self.field, "note.v0")
        self.assertEqual(old["text"], "original note")
        self.assertEqual(old["continuation"]["status"], "incomplete")
        self.assertEqual(old["continuation"]["candidates"], [])

    def test_unplaced_revision_statement_is_not_reported_current(self):
        FileStatementStore(self.field).put(MemoryStatement("staged.only", "unfinished placement", self.new_source, ("revises:note.v1",)))
        continuation = research.describe(self.field, "note.v1")["continuation"]
        self.assertEqual(continuation["status"], "unique")
        self.assertEqual([item["id"] for item in continuation["candidates"]], ["note.v2"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
