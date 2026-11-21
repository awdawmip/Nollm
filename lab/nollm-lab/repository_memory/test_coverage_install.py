"""Verify physical coverage and Git freshness through the portable skill."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

import install_skill


class CoverageInstallTest(unittest.TestCase):
    def test_two_empty_entries_share_one_git_bound_statement(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = install_skill.install(root / "skill") / "scripts/memory.py"

            def run(*args, ok=True):
                result = subprocess.run([sys.executable, "-I", str(script), *map(str, args)],
                                        cwd=root, capture_output=True)
                if ok:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    return json.loads(result.stdout) if args[0] == "coverage" else result.stdout
                self.assertNotEqual(result.returncode, 0, result.stdout)

            def git(*args):
                return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

            def commit(message):
                git("add", "contract.py", "reader.py")
                git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "-c", "commit.gpgSign=false", "commit", "-qm", message)
                return git("rev-parse", "HEAD")

            git("init", "-q")
            (root / "contract.py").write_text("VERSION = 1\n")
            (root / "reader.py").write_text("from contract import VERSION\n")
            rev = commit("source")
            draft = root / "draft.json"
            draft.write_text(json.dumps({"reviewed_commit": rev, "notes": [
                {"key": "shared", "text": "Reader takes the version from contract.",
                 "source": "reader.py", "also": ["contract.py"]},
                {"key": "reader", "text": "Reader imports VERSION.",
                 "source": "reader.py"}]}))
            run("capture", "--draft", draft)
            field = root / "field"
            common = ("coverage", "recall", "--field", field)
            place = ("--place", "shared", "-7", "8", "--place", "reader", "-8", "9")
            result = run("coverage", "build", "--field", field, *place)
            self.assertEqual(result["placed"], 2)
            run("coverage", "build", "--field", field, *place, ok=False)
            for q, r, expected in ((-7, 5, 45056), (-8, 6, 683)):
                entry = ("--entry", -1, q, r, "--direction", "down")
                expansion, = run("coverage", "footprint", *entry)["expansions"]
                self.assertEqual(sum(t["hits"] for t in expansion["targets"]), 96)
                self.assertEqual(sum(t["weight_q16"] for t in expansion["targets"]), 65536)
                target, = (t for t in expansion["targets"] if t["cell"] == [0, -7, 8])
                self.assertEqual(target["weight_q16"], expected)
                items = run(*common, *entry)["items"]
                shared, = (i for i in items if i["id"] == f"shared@{rev}")
                self.assertEqual((shared["score_q16"], shared["path"], shared["cell"]),
                                 (expected, ["coverage_down"], [0, -7, 8]))
                self.assertEqual((shared["status"], shared["source"]), ("current", f"{rev}:reader.py"))
                self.assertEqual(len(shared["context_refs"]), 2)
            back, = run("coverage", "footprint", "--entry", 0, -7, 8, "--direction", "up")["expansions"]
            self.assertEqual([(t["cell"], t["weight_q16"]) for t in back["targets"]],
                             [([-1, -8, 6], 1365), ([-1, -7, 5], 64171)])
            self.assertEqual(run(*common, *entry, "--layer-delta", 0)["items"], [])
            strongest, = run(*common, *entry, "--beam", 1)["items"]
            self.assertEqual(strongest["id"], f"reader@{rev}")
            self.assertEqual(run(*common, "--entry", -1, -7, 5, "--direction", "up")["items"], [])
            self.assertTrue(run(*common, "--entry", -1, -7, 5, "--direction", "both")["items"])

            # Show one page at a time across independent processes. Only a shown
            # ID can open a window; the physical choice is a separate operation.
            state_file = field / "core" / "current_state.json"
            state_before = state_file.read_bytes()
            surface = ("coverage", "surface", "--field", field, "--page-size", 1, "--order", 1)
            first = run(*surface)
            self.assertEqual((first["kind"], first["order"], first["has_more"]), ("surface", 1, True))
            back = first["candidates"][0]["id"]
            run(*surface, "--choose", "surface:unshown", ok=False)
            second = run(*surface, "--choose", "next")
            self.assertNotEqual(second["candidates"][0]["id"], back)
            run(*surface, "--choose", "next", "--choose", back, ok=False)
            choices = ("--choose", "next", "--choose", second["candidates"][0]["id"])
            lower = run(*surface, *choices)
            self.assertEqual((lower["kind"], lower["order"]), ("surface", 0))
            self.assertTrue(lower["candidates"][0]["previews"])
            choices += ("--choose", lower["candidates"][0]["id"])
            candidates = run(*surface, *choices)
            self.assertEqual(candidates["kind"], "physical")
            self.assertNotIn("entry", candidates)
            selected = candidates["candidates"][0]
            entry_result = run(*surface, *choices, "--choose", selected["id"])
            self.assertEqual(entry_result["entry"], selected["physical_cell"])
            self.assertEqual(entry_result["surface_calls"], 4)
            self.assertEqual(run(*surface, "--max-calls", 4, *choices)["pages_left"], 0)
            self.assertEqual(run(*surface, "--max-calls", 4, *choices, "--choose", selected["id"]),
                             entry_result)
            self.assertEqual(state_file.read_bytes(), state_before)
            run(*surface, "--max-calls", 1, "--choose", "next", ok=False)

            (root / "contract.py").write_text("VERSION = 2\n")
            commit("support changed")
            latest = run(*common, *entry)["items"]
            self.assertEqual([i["status"] for i in latest], ["current", "stale"])
            changed = latest[1]
            self.assertNotIn("text", changed)
            self.assertEqual(changed["changes"][0]["path"], "contract.py")
            historical = run(*common, *entry, "--rev", rev)["items"]
            self.assertTrue(all(i["status"] == "current" and i["text"] for i in historical))
            rejected = root / "stale-field"
            run("coverage", "build", "--field", rejected, *place, ok=False)
            self.assertFalse(rejected.exists())


if __name__ == "__main__":
    unittest.main()
