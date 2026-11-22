"""Exercise a project field outside both the source repo and installed runtime."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from install_skill import install


class ProjectMemoryTest(unittest.TestCase):
    def test_installed_project_sources_revision_links_and_runtime_replacement(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "source repo"
            repo.mkdir()
            field = root / "working field"
            first_install = install(root / "runtime one")
            cli = first_install / "scripts/memory.py"

            def execute(args, body=None, *, check=True):
                return subprocess.run(args, cwd=root, input=body, text=True,
                                      capture_output=True, check=check)

            def command(*args, body=None):
                return execute([sys.executable, "-I", str(cli), "project",
                                "--field", str(field), *map(str, args)], body).stdout

            def result(*args, body=None):
                return json.loads(command(*args, body=body))

            git = ["git", "-C", str(repo), "-c", "user.name=Test",
                   "-c", "user.email=test@example.org"]
            execute([*git, "init", "-q"])

            def commit(text):
                (repo / "module.py").write_text(text)
                execute([*git, "add", "module.py"])
                execute([*git, "commit", "-qm", "source update"])
                return execute([*git, "rev-parse", "HEAD"]).stdout.strip()

            old_source = commit("def read():\n    return 'old behavior'\n")
            cite = ["--repo", repo, "--cite", "module.py#L1-L2"]
            result("save", "reading.v1", "--at", 0, 0, *cite,
                   body="Reading path\nThe source returns the old behavior.")
            result("save", "remote", "--at", 40, 0, *cite,
                   body="Remote condition\nReview this condition with the reading path.")
            result("stitch", "reading-to-remote", "reading.v1", "remote")
            link, = result("links")
            self.assertEqual(link["bridge_id"], "reading-to-remote")
            self.assertEqual(result("links", "reading-to-remote"), [link])
            self.assertEqual(result("links", "absent"), [])
            self.assertEqual(command("source", "--id", "reading.v1", "--repo", repo),
                             f"{old_source}:module.py#L1-L2\n1\tdef read():\n2\t    return 'old behavior'\n")

            browse = ["walk", "--order", 0, "--page-size", 1, "--via", "connected"]
            surface_before = result(*browse)
            window, = surface_before["candidates"]
            physical, = result(*browse, window["id"])["candidates"]
            recalled_before = result(*browse, window["id"], physical["id"])
            core_state = field / "core/current_state.json"
            core_before = core_state.read_bytes()
            original = result("show", "reading.v1")

            support_source = commit("def read():\n    return 'old behavior'\n# Independently observed again.\n")
            support_body = "Independent confirmation\nAnother observation supports the same reading behavior."
            saved = result("save", "reading.support", "--reuse", "reading.v1", *cite,
                           "--rev", support_source, "--cite", "module.py#L3", body=support_body)
            self.assertEqual(saved["cell"], [0, 0, 0])
            self.assertEqual(saved["reuses"], "reading.v1")
            support = result("show", "reading.support")
            self.assertEqual(support["text"], support_body)
            self.assertEqual(support["reuses"], "reading.v1")
            self.assertFalse(support["current"])
            self.assertEqual(support["sources"], [f"{support_source}:module.py#L1-L2",
                                                   f"{support_source}:module.py#L3"])
            self.assertEqual(command("source", "--id", "reading.support", "--number", 2, "--repo", repo),
                             f"{support_source}:module.py#L3\n3\t# Independently observed again.\n")
            self.assertEqual(result("show", "reading.v1"), original)
            self.assertEqual(core_state.read_bytes(), core_before)
            self.assertEqual(result("links"), [link])
            self.assertEqual(result(*browse), surface_before)
            self.assertEqual(result(*browse, window["id"], physical["id"]), recalled_before)
            self.assertEqual(result("find", "Independent confirmation"), [])

            # A readable supporting version is not a current revision or reuse target.
            before_invalid = {p.relative_to(field): p.read_bytes() for p in field.rglob("*.json")}
            for choice in ("--reuse", "--revise"):
                with self.subTest(noncurrent_target=choice):
                    invalid = execute([sys.executable, "-I", str(cli), "project", "--field", str(field),
                                       "save", "invalid.support", choice, "reading.support", *map(str, cite)],
                                      "Another expression", check=False)
                    self.assertNotEqual(invalid.returncode, 0)
                    self.assertIn("current", invalid.stderr)
                    self.assertEqual({p.relative_to(field): p.read_bytes() for p in field.rglob("*.json")}, before_invalid)

            new_source = commit("def read():\n    return 'new behavior'\n")
            result("save", "reading.v2", "--revise", "reading.v1", *cite,
                   body="Reading path\nThe source now returns the new behavior.")
            self.assertFalse(result("show", "reading.v1")["current"])
            current = result("show", "reading.v2")
            self.assertTrue(current["current"])
            self.assertEqual(current["revises"], "reading.v1")
            self.assertEqual(current["sources"], [f"{new_source}:module.py#L1-L2"])
            self.assertIn("old behavior", command("source", "--id", "reading.v1", "--repo", repo))
            self.assertEqual(result("show", "reading.support"), support)
            self.assertIn("Independently observed again", command("source", "--id", "reading.support",
                                                                  "--number", 2, "--repo", repo))

            # A separately installed runtime opens the existing user field directly.
            before = {p.relative_to(field): p.read_bytes() for p in field.rglob("*.json")}
            cli = install(root / "runtime two") / "scripts/memory.py"
            self.assertEqual(result("show", "reading.v2"), current)
            self.assertEqual(result("show", "reading.support"), support)
            self.assertEqual(result("links"), [link])
            self.assertEqual({p.relative_to(field): p.read_bytes() for p in field.rglob("*.json")}, before)

            browse = ["walk", "--order", 0, "--page-size", 1, "--via", "connected"]
            window, = result(*browse)["candidates"]
            self.assertEqual(window["previews"], ["Reading path"])
            physical, = result(*browse, window["id"])["candidates"]
            recalled = result(*browse, window["id"], physical["id"])
            self.assertEqual(recalled["entry"], [0, 0, 0])
            self.assertEqual({item["id"] for item in recalled["items"]}, {"reading.v2", "remote"})
            self.assertEqual(next(item["via"] for item in recalled["items"] if item["id"] == "remote"),
                             ["bridge"])
            result("unstitch", "reading-to-remote")
            self.assertEqual(result("links"), [])

            # Project mode has no implicit field or source repository.
            missing_field = execute([sys.executable, "-I", str(cli), "project", "walk"], check=False)
            self.assertEqual(missing_field.returncode, 2)
            self.assertIn("--field", missing_field.stderr)
            missing_repo = execute([sys.executable, "-I", str(cli), "project", "--field", str(field),
                                    "source", "--id", "reading.v2"], check=False)
            self.assertEqual(missing_repo.returncode, 2)
            self.assertIn("--repo", missing_repo.stderr)

            # The EM alias opens the same explicit working field with the same CLI.
            em = [sys.executable, "-I", str(cli), "em", "--field", str(field)]
            self.assertTrue(json.loads(execute([*em, "walk"]).stdout)["candidates"])
            self.assertEqual(json.loads(execute([*em, "show", "reading.v2"]).stdout), current)
            self.assertEqual(json.loads(execute([*em, "links"]).stdout), [])

    def test_save_choices_are_mutually_exclusive(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            cli = install(root / "runtime") / "scripts/memory.py"
            base = [sys.executable, "-I", str(cli), "project", "--field", str(root / "field"),
                    "save", "new", "--repo", str(root), "--cite", "source.md#L1"]
            for choices in (("--at", "0", "0", "--reuse", "current"),
                            ("--revise", "current", "--reuse", "current")):
                with self.subTest(choices=choices):
                    rejected = subprocess.run([*base, *choices], input="body", text=True, capture_output=True)
                    self.assertEqual(rejected.returncode, 2)
                    self.assertIn("not allowed with argument", rejected.stderr)
            self.assertFalse((root / "field").exists())


if __name__ == "__main__":
    unittest.main()
