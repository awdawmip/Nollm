"""Daily storage migration and genuine downward placement through native CLI."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from nollm_access import EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID, FileHandleStore, FileStatementStore
from nollm_core import CoreRuntime, expand_physical_coverage
from coverage_cli import address
from install_skill import install
from project_memory import decide, encounter, main, save_statement, storage


SOURCE = "fixture:storage-and-downward-placement"


class ProjectStorageAndPlacementTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.field = self.root / "field"

    def save(self, identity="root.v1", cell=(0, 0, 0)):
        return save_statement(self.field, identity, "可回到原文的入口。", [SOURCE], cell[1:], None,
                              layer=cell[0], write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)

    def files(self, root=None):
        root = root or self.field
        return {path.relative_to(root): (path.read_bytes(), path.stat().st_mtime_ns)
                for path in root.rglob("*") if path.is_file()}

    def logical_state(self):
        with CoreRuntime(self.field) as core:
            return core.export_state_bytes(), FileHandleStore(self.field).state_bytes()

    def enter(self, **options):
        page = encounter(self.field, order=0, page_size=8, steps=0, prepare_write=True, **options)
        while page["kind"] != "locality":
            candidate, = page["candidates"]
            page = encounter(self.field, [candidate["id"]], cursor=page["cursor"])
        return page

    def test_storage_inspection_does_not_open_runtimes_or_write_files(self):
        self.save()
        before = self.files()
        with patch.object(CoreRuntime, "__init__", side_effect=AssertionError("inspection opened Core")), \
             patch("project_memory.AccessRuntime", side_effect=AssertionError("inspection opened Access")), \
             patch.object(FileHandleStore, "__init__", side_effect=AssertionError("inspection opened bindings")):
            observed = storage(self.field)
        self.assertEqual(observed["status"], "observed")
        self.assertEqual(observed["core"], {"layout": "single_file"})
        self.assertEqual(observed["bindings"], {"layout": "single_file"})
        self.assertEqual(self.files(), before)

        empty = self.root / "empty"
        with CoreRuntime(empty):
            pass
        empty_before = self.files(empty)
        self.assertEqual(storage(empty)["bindings"], {"layout": "single_file"})
        self.assertEqual(self.files(empty), empty_before)
        self.assertFalse((empty / "access").exists())

    def test_explicit_migration_preserves_logical_state_and_is_idempotent(self):
        self.save()
        self.save("far.v1", (0, 200, -100))
        logical = self.logical_state()
        with patch.object(CoreRuntime, "export_state_bytes", side_effect=AssertionError("migration exported all Core")), \
             patch.object(FileHandleStore, "state_bytes", side_effect=AssertionError("migration exported all bindings")):
            migrated = storage(self.field, enable_paged=True, partition_width=8)
        self.assertEqual(migrated["status"], "completed")
        for component in ("core", "bindings"):
            self.assertEqual(migrated[component], {"layout": "paged", "partition_width": 8,
                                                  "migration": "migrated"})
        self.assertEqual(self.logical_state(), logical)
        before = self.files()
        repeated = storage(self.field, enable_paged=True, partition_width=8)
        self.assertEqual(repeated["status"], "completed")
        self.assertEqual(repeated["core"]["migration"], "already_paged")
        self.assertEqual(repeated["bindings"]["migration"], "already_paged")
        self.assertEqual(self.files(), before)
        rejected = storage(self.field, enable_paged=True, partition_width=16)
        self.assertEqual(rejected["status"], "failed")
        self.assertEqual(rejected["core"]["migration"], "failed")
        self.assertEqual(rejected["bindings"]["migration"], "not_attempted")
        self.assertIn("different partition width", rejected["error"]["message"])
        self.assertEqual(self.files(), before)
        with patch.object(CoreRuntime, "__init__", side_effect=AssertionError("inspection opened Core")):
            self.assertEqual(storage(self.field)["core"], {"layout": "paged", "partition_width": 8})
        self.assertEqual(self.files(), before)

    def test_interrupted_second_component_reports_partial_and_same_cli_resumes(self):
        self.save()
        logical = self.logical_state()
        args = ["--field", str(self.field), "storage", "--enable-paged", "--partition-width", "8"]
        output = io.StringIO()
        with patch.object(FileHandleStore, "enable_paged_storage", side_effect=OSError("injected binding failure")), \
             redirect_stdout(output), self.assertRaises(SystemExit) as error:
            main(args)
        self.assertEqual(error.exception.code, 1)
        partial = json.loads(output.getvalue())
        self.assertEqual(partial["status"], "partial")
        self.assertEqual(partial["core"]["migration"], "migrated")
        self.assertEqual(partial["core"]["layout"], "paged")
        self.assertEqual(partial["bindings"]["migration"], "failed")
        self.assertEqual(partial["bindings"]["layout"], "single_file")
        self.assertEqual(partial["error"]["component"], "bindings")
        self.assertIn("injected binding failure", partial["error"]["message"])
        self.assertEqual(self.logical_state(), logical)
        core_before = self.files(self.field / "core")
        output = io.StringIO()
        with redirect_stdout(output):
            main(args)
        completed = json.loads(output.getvalue())
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["core"]["migration"], "already_paged")
        self.assertEqual(completed["bindings"]["migration"], "migrated")
        self.assertEqual(self.files(self.field / "core"), core_before)
        self.assertEqual(self.logical_state(), logical)

    def test_downward_new_rejects_frozen_support_only_witness_before_capture(self):
        self.save(cell=(-2, 0, -2))
        local = self.enter(layers=(-2, -1), surface_layers=(-2,), via="downward")
        parent, child = address(-2, 0, -2), address(-1, -2, -2)
        self.assertNotIn(child, {item.target for item in expand_physical_coverage(parent, "coverage_down").members})
        support = next(item for item in expand_physical_coverage(child, "coverage_up").members
                       if item.target == parent)
        self.assertEqual(support.weight_q16, 683)
        target = next(item for item in local["cells"] if item["id"] == "cell:-1:-2:-2")
        self.assertFalse(target["readable_downward"])
        self.assertFalse(target["at_focus"])
        before = self.files()
        with patch("project_memory.save_statement", side_effect=AssertionError("captured unreachable expression")), \
             self.assertRaisesRegex(ValueError, "reorganization with an actual readable path"):
            decide(self.field, local["cursor"], "new", target["id"], note_id="unreachable.v1",
                   body="应当先选定真实向下可读路径。", sources=[SOURCE])
        self.assertFalse(FileStatementStore(self.field).exists("unreachable.v1"))
        self.assertEqual(self.files(), before)

    def test_downward_new_accepts_current_focus_and_actual_downward_child(self):
        self.save()
        local = self.enter(layers=(0, 1), surface_layers=(0,), via="downward")
        for identity, target in (("focus.v1", "cell:0:0:0"), ("child.v1", "cell:1:0:0")):
            created = decide(self.field, local["cursor"], "new", target, note_id=identity,
                             body="通过当前入口可以读到。", sources=[SOURCE])
            self.assertEqual(created["effect"], "new")
            self.assertTrue(FileStatementStore(self.field).exists(identity))
        descended = encounter(self.field, cursor=local["cursor"], descend="cell:1:0:0")
        self.assertEqual([item["id"] for item in descended["items"]], ["child.v1"])

    def test_other_explicit_kernels_keep_support_only_placement_capability(self):
        self.save(cell=(-2, 0, -2))
        for via in ("local", "connected", "vertical", "lateral"):
            with self.subTest(via=via):
                local = self.enter(layers=(-2, -1), surface_layers=(-2,), via=via)
                candidate = next(item for item in local["cells"] if item["id"] == "cell:-1:-2:-2")
                self.assertFalse(candidate["readable_downward"])
                created = decide(self.field, local["cursor"], "new", candidate["id"],
                                 note_id=f"{via}.v1", body="显式采用另一组传播方式。", sources=[SOURCE])
                self.assertEqual(created["cell"], [-1, -2, -2])

    def test_installed_storage_and_reorganization_cli_complete_real_paged_workflow(self):
        self.save()
        cli = install(self.root / "installed runtime") / "scripts/memory.py"
        cursor_path = self.root / "session.json"
        base = [sys.executable, "-I", str(cli), "project", "--field", str(self.field)]

        help_result = subprocess.run([*base, "storage", "--help"], cwd=self.root,
                                     text=True, capture_output=True, check=True)
        self.assertIn("--enable-paged", help_result.stdout)
        self.assertIn("--partition-width", help_result.stdout)

        def execute(*arguments):
            completed = subprocess.run([*base, *map(str, arguments)], cwd=self.root,
                                       text=True, capture_output=True, check=True)
            return json.loads(completed.stdout)

        def meet(*arguments):
            return execute("encounter", "--cursor-file", cursor_path, *arguments)

        def enter():
            page = meet("--layers", 0, 1, "--surface-layers", 0, "--via", "downward",
                        "--steps", 0, "--order", 0, "--page-size", 8, "--prepare-write")
            while page["kind"] != "locality":
                candidate, = page["candidates"]
                page = meet(candidate["id"])
            return page

        migrated = execute("storage", "--enable-paged")
        self.assertEqual(migrated["status"], "completed")
        self.assertEqual(migrated["core"]["partition_width"], 64)
        self.assertEqual(migrated["bindings"]["migration"], "migrated")
        before = self.files()
        self.assertEqual(execute("storage")["status"], "observed")
        self.assertEqual(self.files(), before)
        enter()
        plan = {
            "schema_version": "nollm_local_reorganization_v1",
            "changes": [
                {"action": "revise", "target": "root.v1", "id": "root.v2",
                 "text": "入口只保留短判断。", "sources": [SOURCE]},
                {"action": "new", "target": "cell:1:0:0", "id": "detail.v1",
                 "text": "沿实际向下覆盖读到完整细节。", "sources": [SOURCE]},
            ],
        }
        plan_path = self.root / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        result = meet("--reorganize", plan_path)
        self.assertEqual(result["commit_state"], "committed")
        self.assertEqual({item["id"] for item in result["readback"]}, {"root.v2", "detail.v1"})
        self.assertFalse(cursor_path.exists())
        old = execute("show", "root.v1")
        self.assertEqual(old["text"], "可回到原文的入口。")
        self.assertFalse(old["current"])
        self.assertEqual(enter()["items"][0]["id"], "root.v2")
        self.assertEqual(meet("--descend", "cell:1:0:0")["items"][0]["id"], "detail.v1")
        self.assertEqual(meet("--recall", "detail.v1")["item"]["sources"], [SOURCE])
        self.assertFalse(cursor_path.exists())


if __name__ == "__main__":
    unittest.main()
