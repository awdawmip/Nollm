"""Exercise a relocated installed field and fixed sources without a Git checkout."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


LAB = Path(__file__).resolve().parent
REPO = LAB.parents[2]
sys.path[:0] = [str(LAB), str(LAB.parent), str(REPO / "packages/nollm-core/src"),
                str(REPO / "packages/nollm-access/src")]

from build_deployment import build
from geometry.rational_geometry import RationalAffine, RationalLayerMap
from nollm_core import GeometryAddress
from project_memory import save
from source_snapshot import SCHEMA, SourceSnapshot


COMMIT = "1234567890abcdef1234567890abcdef12345678"
RUNTIME_COMMIT = "abcdef1234567890abcdef1234567890abcdef12"
BODY = "原文保留。\r\n同一入口可以逐层回读。\r\n"


def snapshot(root, *, partial=False):
    root.mkdir()
    source = root / "files/notes/policy.md"
    source.parent.mkdir(parents=True)
    data = BODY.encode("utf-8")
    source.write_bytes(data)
    metadata = {"blob_sha": hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest(),
                "size": len(data)}
    files = {"notes/policy.md": metadata}
    if partial:
        files["unmaterialized/history.md"] = {"blob_sha": "0" * 40, "size": 111}
    (root / "snapshot.json").write_text(json.dumps({"schema": SCHEMA,
        "repository": "owner/source", "commit": COMMIT, "files": files}), encoding="utf-8")
    return root


class SnapshotSourceTests(unittest.TestCase):
    def test_selected_window_preserves_unicode_and_line_numbers(self):
        with TemporaryDirectory() as tmp:
            source = snapshot(Path(tmp) / "snapshot", partial=True)
            provider = SourceSnapshot(source)
            reference = f"{COMMIT}:notes/policy.md#L2-L2"
            self.assertEqual(provider.excerpt(reference), reference + "\n2\t同一入口可以逐层回读。")
            self.assertEqual(provider.citations(["notes/policy.md#L1-L2"]),
                             [f"{COMMIT}:notes/policy.md#L1-L2"])
            with self.assertRaises(FileNotFoundError):
                provider.excerpt(f"{COMMIT}:unmaterialized/history.md#L1-L1")

    def test_changed_file_and_wrong_commit_are_reported(self):
        with TemporaryDirectory() as tmp:
            source = snapshot(Path(tmp) / "snapshot")
            with self.assertRaisesRegex(ValueError, "requested revision"):
                SourceSnapshot(source).excerpt(f"{'0' * 40}:notes/policy.md#L1-L2")
            (source / "files/notes/policy.md").write_text("Changed original\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "differs from its pinned Git blob"):
                SourceSnapshot(source).excerpt(f"{COMMIT}:notes/policy.md#L1-L1")

    def test_invalid_snapshot_citation_fails_before_field_creation(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = snapshot(root / "snapshot")
            for citation in ("notes/policy.md#L0-L1", "notes/policy.md#L1-L9",
                             "../outside#L1-L1", "unknown.md#L1-L1"):
                with self.subTest(citation=citation), self.assertRaises(ValueError):
                    save(root / "field", None, "HEAD", "note.v1", "A judgment.",
                         [citation], (0, 0), None, snapshot=source)
                self.assertFalse((root / "field").exists())


class PortableDeploymentTests(unittest.TestCase):
    def test_relocated_deployment_reads_revises_and_runs_p8_without_originals(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = snapshot(root / "original source")
            field = root / "original field"
            save(field, None, "HEAD", "notes.v1", "原文保留，同入口沿层读取。",
                 ["notes/policy.md#L1-L2"], (0, 0), None, snapshot=source)
            built = root / "built"
            metadata = build(built, field=field, snapshot=source, runtime_commit=RUNTIME_COMMIT)
            self.assertTrue(metadata["source_materialization"]["complete"])
            self.assertFalse(metadata["automatic_entry_integration"])
            deployment = built.rename(root / "relocated deployment")
            field.rename(root / "unused field")
            source.rename(root / "unused source")
            outside = root / "empty cwd"
            outside.mkdir()

            def command(*args, body=None, as_json=True):
                result = subprocess.run([sys.executable, "-I", str(deployment / "run.py"),
                                         *map(str, args)], cwd=outside, text=True,
                                        input=body, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout) if as_json else result.stdout

            cursor = outside / "session.json"
            page = command("encounter", "--cursor-file", cursor)
            candidate, = page["candidates"]
            local = command("encounter", candidate["id"], "--cursor-file", cursor)
            self.assertEqual([row["id"] for row in local["items"]], ["notes.v1"])
            self.assertIn("原文保留", local["items"][0]["text"])
            revised = command("encounter", "--cursor-file", cursor, "--revise", "notes.v1",
                              "--id", "notes.v2", "--cite", "notes/policy.md#L1-L2",
                              body="判断可修订，原文和旧判断仍可回读。")
            self.assertEqual(revised["effect"], "revision")
            self.assertFalse(cursor.exists())
            old = command("show", "notes.v1")
            self.assertFalse(old["current"])
            self.assertEqual(old["continuation"]["candidates"][0]["id"], "notes.v2")
            original = command("source", "--id", "notes.v1", as_json=False)
            self.assertEqual(original, f"{COMMIT}:notes/policy.md#L1-L2\n1\t原文保留。\n2\t同一入口可以逐层回读。\n")
            direct = command("source", "--at", "notes/policy.md#L2-L2", as_json=False)
            self.assertIn("2\t同一入口可以逐层回读。", direct)

            page = command("encounter", "--cursor-file", cursor)
            command("encounter", page["candidates"][0]["id"], "--cursor-file", cursor)
            recalled = command("encounter", "--cursor-file", cursor, "--recall", "notes.v2")
            self.assertEqual(recalled["item"]["text"], "判断可修订，原文和旧判断仍可回读。")

            frame = RationalLayerMap(RationalAffine.similarity(1, 0)).to_mapping()
            request = {"operation": "coverage", "source": GeometryAddress(
                "default_dream_v1", "default", 1, 0, 0).to_mapping(), "target_layer": 0,
                "source_map": frame, "target_map": frame, "local_length": "1"}
            before = {p.relative_to(deployment / "field"): p.read_bytes()
                      for p in (deployment / "field").rglob("*") if p.is_file()}
            coverage = command("local-p8", "--input", "-", body=json.dumps(request))
            self.assertEqual(coverage["fractional_bits"], 8)
            self.assertEqual(sum(row["hit_count"] for row in coverage["members"]), 96)
            self.assertEqual(before, {p.relative_to(deployment / "field"): p.read_bytes()
                                     for p in (deployment / "field").rglob("*") if p.is_file()})

    def test_partial_snapshot_is_explicit_and_destination_is_not_overwritten(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = snapshot(root / "snapshot", partial=True)
            field = root / "field"
            save(field, None, "HEAD", "note.v1", "A judgment.", ["notes/policy.md#L1-L1"],
                 (0, 0), None, snapshot=source)
            metadata = build(root / "deployment", field=field, snapshot=source,
                             runtime_commit=RUNTIME_COMMIT)
            self.assertEqual(metadata["source_materialization"],
                             {"declared_files": 2, "materialized_files": 1, "complete": False})
            with self.assertRaisesRegex(ValueError, "already exists"):
                build(root / "deployment", field=field, snapshot=source, runtime_commit=RUNTIME_COMMIT)


if __name__ == "__main__":
    unittest.main()
