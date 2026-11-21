"""Exercise shared navigation, local semantic choices, and fresh-process use."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from install_skill import install
from nollm_core import CoreRuntime
from project_memory import decide, describe, encounter, save_statement


SOURCE = "0123456789abcdef0123456789abcdef01234567:module.py#L1-L3"
UPDATED = "89abcdef0123456789abcdef0123456789abcdef:module.py#L2-L4"


class ProjectEncounterTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.field = self.root / "field"

    def empty_locality(self):
        page = encounter(self.field)
        self.assertEqual(page["kind"], "physical")
        candidate, = page["candidates"]
        self.assertEqual(candidate["physical_cell"], [0, 0, 0])
        return encounter(self.field, [candidate["id"]], cursor=page["cursor"])

    def test_empty_field_new_same_cell_support_revision_and_current_recall(self):
        locality = self.empty_locality()
        self.assertEqual(locality["kind"], "locality")
        self.assertEqual(locality["items"], [])
        entry = next(cell for cell in locality["cells"] if cell["cell"] == locality["entry"])
        cursor = locality["cursor"]
        first = decide(self.field, cursor, "new", entry["id"], note_id="read.v1",
                       body="Read behavior\nThe original source result.", sources=[SOURCE])
        self.assertEqual(first["cell"], [0, 0, 0])

        # A distinct fact can share the same native cell; occupancy is not a ban.
        locality = encounter(self.field, cursor=cursor)
        entry = next(cell for cell in locality["cells"] if cell["cell"] == locality["entry"])
        self.assertEqual(entry["native_atoms"], 1)
        decide(self.field, locality["cursor"], "new", entry["id"], note_id="condition",
               body="A separate condition for this behavior.", sources=[SOURCE])
        with CoreRuntime(self.field) as core:
            self.assertEqual(core.placement_count(), 2)
            self.assertEqual(len(core.occupied_cells()), 1)

        before_support = (self.field / "core/current_state.json").read_bytes()
        supported = decide(self.field, cursor, "reuse", "read.v1", note_id="read.support",
                           body="Independent support for the first result.", sources=[UPDATED])
        self.assertEqual(supported["reuses"], "read.v1")
        self.assertEqual((self.field / "core/current_state.json").read_bytes(), before_support)
        self.assertFalse(describe(self.field, "read.support")["current"])

        revised = decide(self.field, cursor, "revision", "read.v1", note_id="read.v2",
                         body="Read behavior\nThe source now gives the updated result.", sources=[UPDATED])
        self.assertEqual(revised["cell"], first["cell"])
        self.assertEqual(revised["revises"], "read.v1")
        self.assertEqual(describe(self.field, "read.v1")["sources"], [SOURCE])
        self.assertFalse(describe(self.field, "read.v1")["current"])
        current = decide(self.field, cursor, "recall", "read.v2")
        self.assertEqual(current["item"]["sources"], [UPDATED])
        self.assertTrue(current["item"]["current"])
        self.assertEqual({item["id"] for item in encounter(self.field, cursor=cursor)["items"]},
                         {"read.v2", "condition"})
        with self.assertRaisesRegex(ValueError, "current fact"):
            decide(self.field, cursor, "revision", "read.v1", note_id="wrong",
                   body="An outdated selection", sources=[SOURCE])
        with CoreRuntime(self.field) as core:
            self.assertEqual(core.placement_count(), 2)

    def test_one_entry_can_expand_and_only_current_local_candidates_are_selected(self):
        locality = self.empty_locality()
        decide(self.field, locality["cursor"], "new", "cell:0:0:0", note_id="entry",
               body="Entry fact", sources=[SOURCE])
        save_statement(self.field, "near", "Two lateral steps away", [SOURCE], (2, 0), None)
        save_statement(self.field, "far", "Outside this locality", [SOURCE], (20, 0), None)
        tight = encounter(self.field, cursor=locality["cursor"], steps=0, via="lateral")
        self.assertEqual([item["id"] for item in tight["items"]], ["entry"])
        expanded = encounter(self.field, cursor=tight["cursor"], steps=2, beam=16, limit=20)
        self.assertEqual(expanded["entry"], tight["entry"])
        self.assertEqual(expanded["budget"]["max_steps"], 2)
        self.assertEqual(expanded["budget"]["beam"], 16)
        self.assertEqual({item["id"] for item in expanded["items"]}, {"entry", "near"})
        near = next(item for item in expanded["items"] if item["id"] == "near")
        self.assertEqual(near["via"], ("lateral", "lateral"))
        with self.assertRaisesRegex(ValueError, "current fact"):
            decide(self.field, expanded["cursor"], "reuse", "far", note_id="wrong",
                   body="Outside the observed locality", sources=[SOURCE])
        with self.assertRaisesRegex(ValueError, "placement cell"):
            decide(self.field, expanded["cursor"], "new", "cell:0:200:0", note_id="wrong",
                   body="Outside the observed locality", sources=[SOURCE])
        with self.assertRaisesRegex(ValueError, "one physical entry"):
            encounter(self.field, ["another-entry"], cursor=expanded["cursor"])
        before = (self.field / "core/current_state.json").read_bytes()
        self.assertEqual(decide(self.field, expanded["cursor"], "none")["effect"], "none")
        self.assertEqual(decide(self.field, expanded["cursor"], "defer")["effect"], "defer")
        self.assertEqual((self.field / "core/current_state.json").read_bytes(), before)

    def test_installed_cli_preserves_encounter_across_processes_and_clears_terminal_cursor(self):
        cli = install(self.root / "runtime") / "scripts/memory.py"
        repo = self.root / "source"
        repo.mkdir()
        git = ["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.org"]

        def run(args, body=None):
            return subprocess.run(args, cwd=self.root, input=body, text=True, capture_output=True, check=True).stdout

        run([*git, "init", "-q"])
        (repo / "source.py").write_text("def read():\n    return 'source result'\n")
        run([*git, "add", "source.py"])
        run([*git, "commit", "-qm", "fixture source"])
        source_commit = run([*git, "rev-parse", "HEAD"]).strip()
        cursor_file = self.root / "encounter.json"
        base = [sys.executable, "-I", str(cli), "project", "--field", str(self.field)]

        def meet(*args, body=None):
            return json.loads(run([*base, "encounter", "--cursor-file", str(cursor_file),
                                   *map(str, args)], body))

        def enter():
            page = meet()
            while page["kind"] != "locality":
                page = meet(page["candidates"][0]["id"])
            return page

        locality = enter()
        self.assertEqual(locality["entry"], [0, 0, 0])
        self.assertTrue(cursor_file.exists())
        cite = ("--repo", repo, "--cite", "source.py#L1-L2")
        created = meet("--new", "cell:0:0:0", "--id", "result.v1", *cite, body="Result\nFirst expression.")
        self.assertEqual(created["effect"], "new")
        self.assertFalse(cursor_file.exists())

        locality = enter()
        self.assertEqual(locality["items"][0]["sources"], [f"{source_commit}:source.py#L1-L2"])
        expanded = meet("--steps", 2, "--beam", 32, "--via", "lateral", "--limit", 10)
        self.assertEqual(expanded["entry"], locality["entry"])
        self.assertEqual(expanded["budget"]["beam"], 32)
        reused = meet("--reuse", "result.v1", "--id", "result.support", *cite, body="Independent expression.")
        self.assertEqual(reused["effect"], "reuse")
        self.assertFalse(cursor_file.exists())

        enter()
        revised = meet("--revise", "result.v1", "--id", "result.v2", *cite, body="Result\nCorrected expression.")
        self.assertEqual(revised["effect"], "revision")
        self.assertFalse(cursor_file.exists())
        enter()
        recalled = meet("--recall", "result.v2")
        self.assertEqual(recalled["item"]["text"], "Result\nCorrected expression.")
        self.assertFalse(cursor_file.exists())
        old = json.loads(run([*base, "show", "result.v1"]))
        self.assertFalse(old["current"])
        self.assertIn("return 'source result'", run([*base, "source", "--id", "result.v1", "--repo", str(repo)]))
        enter()
        self.assertEqual(meet("--none")["effect"], "none")
        self.assertFalse(cursor_file.exists())
        self.assertEqual(meet()["kind"], "surface")
        self.assertEqual(meet("--defer")["effect"], "defer")
        self.assertFalse(cursor_file.exists())


if __name__ == "__main__":
    unittest.main()
