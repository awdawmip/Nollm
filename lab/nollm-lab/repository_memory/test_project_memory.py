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

            new_source = commit("def read():\n    return 'new behavior'\n")
            result("save", "reading.v2", "--revise", "reading.v1", *cite,
                   body="Reading path\nThe source now returns the new behavior.")
            self.assertFalse(result("show", "reading.v1")["current"])
            current = result("show", "reading.v2")
            self.assertTrue(current["current"])
            self.assertEqual(current["revises"], "reading.v1")
            self.assertEqual(current["sources"], [f"{new_source}:module.py#L1-L2"])
            self.assertIn("old behavior", command("source", "--id", "reading.v1", "--repo", repo))

            # A separately installed runtime opens the existing user field directly.
            before = {p.relative_to(field): p.read_bytes() for p in field.rglob("*.json")}
            cli = install(root / "runtime two") / "scripts/memory.py"
            self.assertEqual(result("show", "reading.v2"), current)
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

            # The EM adapter retains its supplied default field and exposes the same link CLI.
            em = [sys.executable, "-I", str(cli), "em"]
            self.assertTrue(json.loads(execute([*em, "walk"]).stdout)["candidates"])
            self.assertIsInstance(json.loads(execute([*em, "links"]).stdout), list)


if __name__ == "__main__":
    unittest.main()
