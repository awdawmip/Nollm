"""Run the installed, relocated skill against an unrelated repository."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class InstalledSkillTest(unittest.TestCase):
    def test_native_encounter_is_independent_of_auxiliary_retrieval(self):
        installer = Path(__file__).with_name("install_skill.py").resolve()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            installed = root / "installed"
            subprocess.run([sys.executable, "-I", str(installer), "--dest", str(installed)],
                           check=True, capture_output=True)
            skill = installed.rename(root / "relocated skill")
            cli = skill / "scripts/memory.py"
            runtime = skill / "scripts/runtime"
            for name in ("task_recall.py", "machine_field.py", "router.py", "facts.py",
                         "records.py", "geometry_cli.py", "native_geo.py"):
                (runtime / name).unlink()
            self.assertTrue((skill / "references/auxiliary.md").is_file())

            repo = root / "source"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / "reader.py").write_text("def read():\n    return 42\n")
            subprocess.run(["git", "-C", str(repo), "add", "reader.py"], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test",
                            "-c", "user.email=test@example.invalid", "-c", "commit.gpgSign=false",
                            "commit", "-qm", "source"], check=True)
            # A native field neither reads this old manifest nor rebuilds a
            # lexical/source-layout field when the manifest is unusable.
            (repo / ".nollm").mkdir()
            (repo / ".nollm/repository-notes.json").write_text("unusable legacy manifest")
            field = root / "project field"
            cursor = root / "encounter.json"

            def project(*args, body=None, as_json=True):
                result = subprocess.run([sys.executable, "-I", str(cli), "project", "--field",
                                         str(field), *map(str, args)], cwd=repo, text=True,
                                        input=body, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout) if as_json else result.stdout

            def encounter(*args, **kwargs):
                return project("encounter", "--cursor-file", cursor, *args, **kwargs)

            empty = encounter()
            self.assertEqual(empty["kind"], "physical")
            self.assertNotIn("entry", empty)
            local = encounter(empty["candidates"][0]["id"])
            self.assertEqual(local["kind"], "locality")
            self.assertEqual(local["items"], [])
            origin = next(cell for cell in local["cells"] if cell["cell"] == local["entry"])
            written = encounter("--new", origin["id"], "--id", "reader.v1",
                                "--repo", repo, "--cite", "reader.py#L1-L2",
                                body="Reading returns the source-defined value 42.")
            self.assertEqual((written["effect"], written["cell"]), ("new", local["entry"]))
            self.assertFalse(cursor.exists())

            page = encounter()
            observed = []
            while page["kind"] != "locality":
                observed.append(page["kind"])
                self.assertNotIn("entry", page)
                page = encounter(page["candidates"][0]["id"])
            self.assertIn("surface", observed)
            self.assertIn("physical", observed)
            self.assertEqual([item["id"] for item in page["items"]], ["reader.v1"])
            recalled = encounter("--recall", "reader.v1")
            self.assertEqual(recalled["effect"], "recall")
            self.assertEqual(recalled["item"]["text"], "Reading returns the source-defined value 42.")
            source = project("source", "--id", "reader.v1", "--repo", repo, as_json=False)
            self.assertIn("2\t    return 42", source)
            self.assertFalse((repo / ".git/nollm-repository-memory").exists())
            self.assertFalse((field / "route.json").exists())

    def test_legacy_commands_require_an_explicit_workflow(self):
        cli = Path(__file__).parent / "skills/nollm-repository-memory/scripts/memory.py"
        for old, replacement in (("recall", "baseline recall"), ("field", "baseline field"),
                                 ("brief", "aux brief"), ("route", "aux route"),
                                 ("geometry", "aux aoci"), ("geometry-native", "aux aoci-field")):
            with self.subTest(command=old):
                result = subprocess.run([sys.executable, "-I", str(cli), old, "--help"],
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn(replacement, result.stderr)
                self.assertIn("project --field FIELD encounter", result.stderr)

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

    def test_portable_explicit_baseline_lifecycle(self):
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
            self.assertTrue((skill / "references/auxiliary.md").is_file())
            repo = root / "separate project"
            repo.mkdir()

            def git(*args):
                return subprocess.check_output(["git", *args], cwd=repo).decode().strip()

            def commit():
                git("add", "emitter.py", "formatter.py")
                git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "-c", "commit.gpgSign=false", "commit", "-qm", "example")
                return git("rev-parse", "HEAD")

            def memory(namespace, command, *args, host_skill=skill):
                # Isolated Python drops PYTHONPATH and the source checkout.
                return subprocess.check_output(
                    [sys.executable, "-I", str(host_skill / "scripts" / "memory.py"), namespace, command,
                     "--repo", str(repo), *args], cwd=repo)

            git("init", "-q")
            (repo / "emitter.py").write_text("from formatter import SUFFIX\n")
            support = repo / "formatter.py"
            support.write_bytes(b'SUFFIX = "!"\r\n')
            first = commit()
            scope = json.loads(memory("aux", "inventory", "--scope", "."))
            self.assertEqual(scope["counts"]["unrecorded"], 2)
            draft = root / "draft.json"
            text = "Emitter imports the suffix from formatter."
            draft.write_text(json.dumps({"reviewed_commit": first, "notes": [
                {"key": "emitter.suffix", "text": text, "source": "emitter.py",
                 "also": ["formatter.py"]}]}))
            memory("aux", "capture", "--draft", str(draft))
            self.assertTrue((repo / ".nollm" / "repository-notes.json").is_file())
            recall = ("--query", "emitter suffix")
            ephemeral = memory("baseline", "recall", *recall, "--no-cache", "--format", "view")
            cache = Path(git("rev-parse", "--absolute-git-dir")) / "nollm-repository-memory" / "fields-v1"
            self.assertFalse(cache.exists())
            hit = json.loads(memory("baseline", "recall", *recall, host_skill=claude))
            self.assertTrue(cache.is_dir())
            self.assertEqual(hit["mode"], "lexical_source_layout_baseline")
            self.assertIn(text, ephemeral.decode())
            self.assertEqual(memory("baseline", "recall", *recall, "--format", "view"), ephemeral)
            self.assertEqual((hit["entry_key"], hit["matches"][0]["text"]), ("emitter.suffix", text))
            source = ("--key", "emitter.suffix", "--evidence-index", "1")
            original = subprocess.check_output(["git", "show", f"{first}:formatter.py"], cwd=repo)
            self.assertEqual(memory("aux", "source", *source), original)
            support.write_text('SUFFIX = "?"\n')
            commit()
            self.assertEqual(json.loads(memory("baseline", "recall", *recall, host_skill=claude))["matches"], [])
            stale = json.loads(memory("aux", "review", host_skill=claude))["notes"][0]
            self.assertEqual((stale["status"], stale["changes"][0]["path"]), ("stale", "formatter.py"))
            self.assertEqual(memory("aux", "source", *source, "--rev", first), original)


if __name__ == "__main__":
    unittest.main()
