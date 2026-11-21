"""Exercise the machine commands from a relocated skill against a small, unrelated project."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class InstalledMachineCorpus(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "example project"
        self.repo.mkdir()
        self.git("init", "-q")
        src = self.repo / "src/example"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text("", encoding="utf-8")
        (src / "decoder.py").write_text("def decode_revision_stamp():\n    return 1\n", encoding="utf-8")
        (src / "reader.py").write_text("from .decoder import decode_revision_stamp\n", encoding="utf-8")
        (self.repo / "label.js").write_text("export const formatStamp = revision => String(revision);\n",
                                          encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "initial tree")
        self.rev = self.git("rev-parse", "HEAD")
        self.facts = self.root / "facts"
        self.records = self.root / "records.jsonl"
        self.field = self.root / "native"
        installer = Path(__file__).resolve().with_name("install_skill.py")
        staging = self.root / "new skill"
        subprocess.run([sys.executable, "-I", str(installer), "--dest", str(staging)],
                       check=True, capture_output=True, cwd=self.root)
        self.cli = staging.rename(self.root / "relocated") / "scripts/memory.py"

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), "-c", "user.name=Test",
                                       "-c", "user.email=test@example.invalid", "-c", "commit.gpgSign=false",
                                       *args], text=True).strip()

    def run_tool(self, namespace, command, *args, success=True):
        proc = subprocess.run([sys.executable, "-I", str(self.cli), namespace, command,
                              *map(str, args)], cwd=self.root, text=True, capture_output=True)
        if success:
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return proc.stdout
        self.assertNotEqual(proc.returncode, 0)
        return proc.stderr

    def test_explicit_source_routing_baseline_and_evidence(self):
        repo_at = ["--repo", self.repo, "--rev", self.rev]
        self.run_tool("aux", "facts", *repo_at, "--out", self.facts)
        edges = [json.loads(s) for s in (self.facts / "edges.jsonl").read_text().splitlines()]
        src, dst = "src/example/reader.py", "src/example/decoder.py"
        self.assertTrue(any((e["src"], e["dst"], e["confidence"], e["line"]) ==
                            (src, dst, "exact", 1) for e in edges))
        marks = self.root / "check.jsonl"
        symbol = {"kind": "symbol", "id": "decoder", "qualname": "decode_revision_stamp",
                  "symbol_kind": "py_function", "line": 1, "path": dst,
                  "blob": self.git("rev-parse", f"{self.rev}:{dst}")}
        proposals = [symbol, dict(symbol, id="wrong", line=2), dict(symbol, id="bad", qualname=[])]
        marks.write_text("".join(json.dumps(m) + "\n" for m in proposals))
        checks = json.loads(self.run_tool("aux", "check-marks", *repo_at, "--marks", marks))
        self.assertEqual([r["status"] for r in checks["results"]], ["verified", "unsupported", "invalid"])
        symbols = (json.loads(line) for line in (self.facts / "symbols.jsonl").read_bytes().splitlines())
        arrow = next(item for item in symbols if item["path"] == "label.js" and item["name"] == "formatStamp")
        marks.write_text(json.dumps({"id":"arrow", "kind":"symbol", "path":arrow["path"],
                                     "blob":arrow["blob"], "line":arrow["line"], "qualname":arrow["qualname"],
                                     "symbol_kind":arrow["kind"]}) + "\n")
        checks = json.loads(self.run_tool("aux", "check-marks", *repo_at, "--marks", marks))
        self.assertEqual(checks["results"][0]["status"], "candidate")
        note = {"key": "reader.decoder", "text": "The reader imports the revision-stamp decoder.",
                "reviewed_commit": self.rev,
                "evidence": [{"path": path, "blob": self.git("rev-parse", f"{self.rev}:{path}")}
                             for path in (src, dst)]}
        manifest = self.root / "notes.json"
        manifest.write_text(json.dumps({"schema": "nollm_repo_notes_v1", "notes": [note]}))
        claims = self.root / "claims.json"
        self.run_tool("aux", "records", *repo_at, "--manifest", manifest, "--claim-template", "--out", claims)
        template = json.loads(claims.read_bytes())
        template["reader.decoder"]["atoms"] = [["reader", "imports", "decode_revision_stamp"]]
        claims.write_text(json.dumps(template))
        self.run_tool("aux", "records", *repo_at, "--manifest", manifest, "--claims", claims, "--out", self.records)
        row = json.loads(self.records.read_bytes())
        self.assertNotIn(note["text"], self.records.read_text())
        self.assertEqual(row["symbol_anchors"][0]["symbol"], "decode_revision_stamp")
        seeds = self.root / "seeds.json"
        self.run_tool("aux", "route", *repo_at, "--facts", self.facts, "--records", self.records,
                      "--mode", "semantic", "--query", "decode_revision_stamp", "--out", seeds)
        batch = json.loads(seeds.read_bytes())
        self.assertEqual(batch["commit"], self.rev)
        self.assertIn(dst, batch["results"][0]["paths"])
        args = ["build", *repo_at, "--facts", self.facts, "--records", self.records,
                "--layout", "architecture", "--field", self.field]
        self.run_tool("baseline", "field", *args)
        def read():
            return json.loads(self.run_tool("baseline", "field", "query", *repo_at, "--field", self.field,
                                            "--seeds", seeds, "--include-records"))
        result = read()
        self.assertEqual(result["mode"], "source_routed_architecture_baseline")
        hit = result["results"][0]
        self.assertEqual(hit["records"], [row])
        self.assertEqual(set(hit["paths"]), {src, dst})
        self.assertEqual(read()["results"][0], hit)
        (self.repo / src).write_text("def read():\n    pass\n", encoding="utf-8")
        self.git("commit", "-qam", "change reader")
        batch["commit"] = self.git("rev-parse", "HEAD")
        seeds.write_text(json.dumps(batch), encoding="utf-8")
        self.run_tool("baseline", "field", "query", *repo_at, "--field", self.field, "--seeds", seeds, success=False)
        self.run_tool("baseline", "field", "query", "--repo", self.repo, "--field", self.field,
                      "--seeds", seeds, success=False)
        self.run_tool("aux", "route", "--repo", self.repo, "--rev", "HEAD", "--facts", self.facts,
                      "--mode", "lexical", "--query", "decoder", success=False)


if __name__ == "__main__":
    unittest.main()
