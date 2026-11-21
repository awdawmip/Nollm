"""Exercise the installed research entry, including an in-place correction."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from install_skill import install


class ResearchMemoryTest(unittest.TestCase):
    def test_source_windows_and_current_neighborhood_across_reopens(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            cli = install(root / "skill") / "scripts/memory.py"
            base = [sys.executable, "-I", str(cli), "em"]

            def run(command, body=None):
                return subprocess.run(command, cwd=root, input=body, capture_output=True,
                                      encoding="utf-8", check=True).stdout

            # The installation ships an authored field, independently of this test repository.
            self.assertTrue(json.loads(run([*base, "walk"]))["candidates"])
            field = [*base, "--field", str(root / "new field")]
            git = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.org"]

            def commit(text):
                (root / "lemma.md").write_text(text, encoding="utf-8")
                run([*git, "add", "lemma.md"])
                run([*git, "commit", "-qm", "update lemma"])
                return run([*git, "rev-parse", "HEAD"]).strip()

            run([*git, "init", "-q"])
            first = commit("lemma\n旧条件\nold proof\nend\n")
            cite = ["--repo", str(root), "--cite", "lemma.md#L2"]
            run([*field, "save", "lemma.1", "--at", "0", "0", *cite], "Old claim\n旧条件")
            run([*field, "save", "proof", "--at", "1", "0", *cite], "Neighbor")
            run([*field, "save", "distant", "--at", "8", "0", *cite], "Other question")
            latest = commit("lemma\n新条件\nnew proof\nend\n")
            run([*field, "save", "lemma.2", "--revise", "lemma.1", *cite,
                 "--cite", "lemma.md#L2-L3"], "New claim\n新条件")

            self.assertFalse(json.loads(run([*field, "show", "lemma.1"]))["current"])
            current = json.loads(run([*field, "show", "lemma.2"]))
            self.assertTrue(current["current"])
            self.assertEqual(current["revises"], "lemma.1")
            source = [*field, "source", "--repo", str(root)]
            self.assertEqual(run([*source, "--id", "lemma.1"]),
                             f"{first}:lemma.md#L2\n2\t旧条件\n")
            self.assertEqual(run([*source, "--id", "lemma.2", "--number", "2"]),
                             f"{latest}:lemma.md#L2-L3\n2\t新条件\n3\tnew proof\n")
            self.assertEqual(json.loads(run([*field, "find", "claim"])),
                             [{"id": "lemma.2", "preview": "New claim"}])

            walk = [*field, "walk", "--order", "0", "--page-size", "1"]
            window, = json.loads(run(walk))["candidates"]
            self.assertEqual(window["previews"], ["New claim"])
            cells = json.loads(run([*walk, window["id"]]))
            entry, = cells["candidates"]
            hits = json.loads(run([*walk, window["id"], entry["id"]]))
            self.assertEqual(hits["entry"], [0, 0, 0])
            self.assertEqual({item["id"]: item["text"] for item in hits["items"]},
                             {"lemma.2": "New claim\n新条件", "proof": "Neighbor"})

            # A fresh CLI process resumes each page; candidate IDs and recall
            # match replay, including after the first page of a scan.
            run([*field, "save", "far", "--at", "8", "-3", *cite], "Remote evidence")
            bookmark = root / "walk.json"
            browse = [*walk, "--cursor-file", str(bookmark)]
            json.loads(run(browse))
            continued = json.loads(run([*browse, "next"]))
            self.assertEqual(continued, json.loads(run([*walk, "next"])))
            selected = continued["candidates"][0]["id"]
            physical = json.loads(run([*browse, selected]))
            expected = json.loads(run([*walk, "next", selected]))
            self.assertEqual(physical, expected)
            leaf = physical["candidates"][0]["id"]
            self.assertEqual(json.loads(run([*browse, leaf])), json.loads(run([*walk, "next", selected, leaf])))
            self.assertFalse(bookmark.exists())

            connected = [*walk, "--via", "connected", window["id"], entry["id"]]
            before = json.loads(run(connected))
            run([*field, "stitch", "lead", "lemma.2", "far"])
            linked = json.loads(run(connected))
            self.assertEqual(linked["entry"], before["entry"])
            self.assertEqual(next(i["via"] for i in linked["items"] if i["id"] == "far"), ["bridge"])
            self.assertEqual(json.loads(run([*walk, window["id"], entry["id"]])), hits)
            run([*field, "unstitch", "lead"])
            self.assertEqual(json.loads(run(connected)), before)


if __name__ == "__main__":
    unittest.main()
