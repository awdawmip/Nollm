"""Run the installed, relocated skill against an unrelated repository."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class InstalledSkillTest(unittest.TestCase):
    def test_host_scopes_and_existing_skill(self):
        installer = Path(__file__).with_name("install_skill.py").resolve()
        with TemporaryDirectory() as tmp:
            home = Path(tmp) / "user"
            project = Path(tmp) / "target project"
            nested = project / "src"
            nested.mkdir(parents=True)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            for host, user_dir, repo_dir in (("codex", ".agents", ".agents"),
                                              ("claude", ".claude", ".claude"),
                                              ("copilot", ".copilot", ".github")):
                for args, parent in (([], home / user_dir),
                                     (["--scope", "repo", "--repo", str(nested)], project / repo_dir)):
                    with self.subTest(host=host, args=args):
                        cmd = [sys.executable, "-I", str(installer), "--host", host, *args]
                        env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
                        result = subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, text=True, check=True)
                        skill = parent / "skills" / "nollm-repository-memory"
                        self.assertEqual(Path(result.stdout.strip()), skill)
                        self.assertTrue((skill / "scripts" / "memory.py").is_file())
                        descriptor = skill / "SKILL.md"
                        self.assertIn("name: nollm-repository-memory", descriptor.read_text(encoding="utf-8"))
                        descriptor.write_text("local edits", encoding="utf-8")
                        again = subprocess.run(cmd, cwd=tmp, env=env, capture_output=True)
                        self.assertEqual(again.returncode, 2)
                        self.assertEqual(descriptor.read_text(encoding="utf-8"), "local edits")
                        if host == "codex":
                            alias = [sys.executable, "-I", str(installer), "--host", "opencode", *args]
                            shared = subprocess.run(alias, cwd=tmp, env=env, capture_output=True, text=True)
                            self.assertEqual(shared.returncode, 2)
                            self.assertIn(f"destination already exists: {skill}", shared.stderr)

    def test_portable_lifecycle(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = root / "skill install" / "nollm-repository-memory"
            installer = Path(__file__).resolve().with_name("install_skill.py")
            install = [sys.executable, "-I", str(installer), "--dest", str(installed)]
            subprocess.run(install, cwd=root, check=True, capture_output=True)
            again = subprocess.run(install, cwd=root, capture_output=True)
            self.assertEqual(again.returncode, 2)
            # Move the standalone installation into Codex's personal discovery directory.
            home = root / "another home"
            codex_root = home / ".agents" / "skills"
            codex_root.mkdir(parents=True)
            skill = installed.rename(codex_root / installed.name)
            claude = Path(subprocess.check_output(
                [sys.executable, "-I", str(installer), "--host", "claude"], cwd=root,
                env=dict(os.environ, HOME=str(home), USERPROFILE=str(home)), text=True).strip())
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

            def memory(command, *args, host_skill=skill):
                # Isolated Python drops PYTHONPATH and the source checkout.
                return subprocess.check_output(
                    [sys.executable, "-I", str(host_skill / "scripts" / "memory.py"), command,
                     "--repo", str(repo), *args], cwd=repo)

            git("init", "-q")
            (repo / "emitter.py").write_text("from formatter import SUFFIX\n")
            support = repo / "formatter.py"
            support.write_bytes(b'SUFFIX = "!"\r\n')
            first = commit()
            scope = json.loads(memory("inventory", "--scope", "."))
            self.assertEqual(scope["counts"]["unrecorded"], 2)
            draft = root / "draft.json"
            text = "Emitter imports the suffix from formatter."
            draft.write_text(json.dumps({"reviewed_commit": first, "notes": [
                {"key": "emitter.suffix", "text": text, "source": "emitter.py",
                 "also": ["formatter.py"]}]}))
            memory("capture", "--draft", str(draft))
            self.assertTrue((repo / ".nollm" / "repository-notes.json").is_file())
            recall = ("--query", "emitter suffix")
            ephemeral = memory("recall", *recall, "--no-cache", "--format", "view")
            cache = Path(git("rev-parse", "--absolute-git-dir")) / "nollm-repository-memory" / "fields-v1"
            self.assertFalse(cache.exists())
            hit = json.loads(memory("recall", *recall, host_skill=claude))
            self.assertTrue(cache.is_dir())
            self.assertIn(text, ephemeral.decode())
            self.assertEqual(memory("recall", *recall, "--format", "view"), ephemeral)
            self.assertEqual((hit["entry_key"], hit["matches"][0]["text"]), ("emitter.suffix", text))
            source = ("--key", "emitter.suffix", "--evidence-index", "1")
            original = subprocess.check_output(["git", "show", f"{first}:formatter.py"], cwd=repo)
            self.assertEqual(memory("source", *source), original)
            support.write_text('SUFFIX = "?"\n')
            commit()
            self.assertEqual(json.loads(memory("recall", *recall, host_skill=claude))["matches"], [])
            stale = json.loads(memory("review", host_skill=claude))["notes"][0]
            self.assertEqual((stale["status"], stale["changes"][0]["path"]), ("stale", "formatter.py"))
            self.assertEqual(memory("source", *source, "--rev", first), original)


if __name__ == "__main__":
    unittest.main()
