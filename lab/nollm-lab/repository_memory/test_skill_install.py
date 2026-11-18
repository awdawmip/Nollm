"""Run the installed, relocated skill against an unrelated repository."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class InstalledSkillTest(unittest.TestCase):
    def test_portable_lifecycle(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = root / "skill install" / "nollm-repository-memory"
            installer = Path(__file__).resolve().with_name("install_skill.py")
            install = [sys.executable, "-I", str(installer), "--dest", str(installed)]
            subprocess.run(install, cwd=root, check=True, capture_output=True)
            again = subprocess.run(install, cwd=root, capture_output=True)
            self.assertEqual(again.returncode, 2)
            skill = installed.rename(root / "relocated skill")
            self.assertIn("name: nollm-repository-memory", (skill / "SKILL.md").read_text())
            self.assertTrue((skill / "LICENSE").is_file())
            repo = root / "separate project"
            repo.mkdir()

            def git(*args):
                return subprocess.check_output(["git", *args], cwd=repo).decode().strip()

            def commit():
                git("add", "emitter.py", "formatter.py")
                git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "-c", "commit.gpgSign=false", "commit", "-qm", "example")
                return git("rev-parse", "HEAD")

            def memory(command, *args):
                # Isolated Python drops PYTHONPATH and the source checkout.
                return subprocess.check_output(
                    [sys.executable, "-I", str(skill / "scripts" / "memory.py"), command,
                     "--repo", str(repo), *args], cwd=repo)

            git("init", "-q")
            (repo / "emitter.py").write_text("from formatter import SUFFIX\n")
            support = repo / "formatter.py"
            support.write_bytes(b'SUFFIX = "!"\r\n')
            first = commit()
            scope = json.loads(memory("inventory", "--scope", "."))
            self.assertEqual(scope["counts"]["unrecorded"], 2)
            draft = root / "draft.json"
            manifest = ("--manifest", str(repo / ".nollm" / "notes.json"))
            text = "Emitter imports the suffix from formatter."
            draft.write_text(json.dumps({"reviewed_commit": first, "notes": [
                {"key": "emitter.suffix", "text": text, "source": "emitter.py",
                 "also": ["formatter.py"]}]}))
            memory("capture", *manifest, "--draft", str(draft))
            recall = (*manifest, "--query", "emitter suffix")
            hit = json.loads(memory("recall", *recall))
            self.assertEqual((hit["entry_key"], hit["matches"][0]["text"]), ("emitter.suffix", text))
            source = (*manifest, "--key", "emitter.suffix", "--evidence-index", "1")
            original = subprocess.check_output(["git", "show", f"{first}:formatter.py"], cwd=repo)
            self.assertEqual(memory("source", *source), original)
            support.write_text('SUFFIX = "?"\n')
            commit()
            self.assertEqual(json.loads(memory("recall", *recall))["matches"], [])
            stale = json.loads(memory("review", *manifest))["notes"][0]
            self.assertEqual((stale["status"], stale["changes"][0]["path"]), ("stale", "formatter.py"))
            self.assertEqual(memory("source", *source, "--rev", first), original)


if __name__ == "__main__":
    unittest.main()
