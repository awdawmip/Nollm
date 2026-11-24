"""Local file I/O, logical compatibility and interrupted-page recovery."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nollm_core import (
    AtomHandle, CoreRecallRequest, CoreRuntime, GeometryAddress, MemoryAtom,
    MoveCommand, PhysicalFieldScope, PutCommand, RecallBudget, ReplaceCommand,
)
from nollm_core import paged_storage


def cell(layer=0, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


class PagedStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def make_field(self):
        with CoreRuntime(self.root) as core:
            first = core.put(MemoryAtom("first", "表层短判断"), cell(-2))
            second = core.put(MemoryAtom("second", "detail"), cell(0, 70, 1))
            third = core.put(MemoryAtom("third", "another"), cell(0, -70, 1))
            logical = core.export_state_bytes()
            self.assertEqual(logical, core.state_path.read_bytes())
            core.enable_paged_storage()
            self.assertEqual(logical, core.export_state_bytes())
        return first, second, third, logical

    def test_legacy_migration_logical_export_reopen_and_commands(self):
        first, second, third, logical = self.make_field()
        with CoreRuntime(self.root) as core:
            self.assertEqual(core.storage_layout, "paged")
            self.assertEqual(core.export_state_bytes(), logical)
            moved, _ = core.apply_batch((MoveCommand(second, cell(0, 150, 1)),
                                        ReplaceCommand(first, "新表层判断")))
            self.assertFalse(core.contains(second))
            self.assertEqual(core.get(moved).payload_utf8, "detail")
            self.assertEqual(core.remove(third).payload_utf8, "another")
            expected = core.export_state_bytes()
        with CoreRuntime(self.root) as core:
            self.assertEqual(core.export_state_bytes(), expected)
            self.assertEqual(core.placement_count(), 2)

    def test_surface_and_totals_do_not_load_deep_bodies(self):
        self.make_field()
        with CoreRuntime(self.root) as core:
            core.put(MemoryAtom("large", "长" * 200_000), cell(2, 1000, 0))
        reads = []
        original = Path.read_bytes

        def observed(path):
            reads.append(path)
            return original(path)

        with patch.object(Path, "read_bytes", observed):
            with CoreRuntime(self.root) as core:
                scope = PhysicalFieldScope("default_dream_v1", "default", (-2,), -2)
                page = core.surface_page(scope, 0, None, 8)
                self.assertEqual(page.cells[0].native_atom_count, 1)
                self.assertEqual(core.layer_content_totals(-2), (1, len("表层短判断".encode())))
                self.assertEqual(core.occupied_cells(scope=scope), (cell(-2),))
                self.assertEqual(core.atoms_at(cell(-2))[0][1].payload_utf8, "表层短判断")
        bodies = [path for path in reads if "pages" in path.parts and not path.name.endswith(".meta.json")]
        self.assertEqual(len(bodies), 1)
        self.assertIn("-2", bodies[0].parts)
        self.assertFalse(any("2" in path.relative_to(self.root / "core/pages").parts[2:3]
                             for path in reads if "pages" in path.parts))

    def test_local_write_replaces_only_its_partition_files(self):
        _, second, _, _ = self.make_field()
        writes = []
        original = paged_storage._atomic_write

        def observed(path, payload):
            writes.append(path)
            return original(path, payload)

        with CoreRuntime(self.root) as core:
            with patch.object(paged_storage, "_atomic_write", observed):
                core.replace(second, "revised detail")
        page_writes = [path for path in writes if "pages" in path.parts]
        self.assertEqual({path.name for path in page_writes}, {"1_0.json", "1_0.meta.json"})
        self.assertEqual(len(page_writes), 2)
        self.assertFalse(any(path.name in {"current_state.json", "bridges.json"} for path in writes))

    def test_local_snapshot_restores_empty_and_populated_cells_only(self):
        first, second, _, _ = self.make_field()
        empty = cell(-2, 70, 0)
        with CoreRuntime(self.root) as core:
            neighbor = core.put(MemoryAtom("neighbor", "same partition"), cell(-2, 1, 0))
            snapshot = core.export_cell_state((first.geometry_address, empty))
            self.assertLess(len(snapshot), 900)
            core.move(first, empty)
            core.replace(second, "unrelated new value")
            core.replace(neighbor, "same partition new value")
            core.import_cell_state(snapshot)
            self.assertEqual(core.get(first).payload_utf8, "表层短判断")
            self.assertEqual(core.atoms_at(empty), ())
            self.assertEqual(core.get(second).payload_utf8, "unrelated new value")
            self.assertEqual(core.get(neighbor).payload_utf8, "same partition new value")

    def test_failure_after_commit_cleanup_still_restores_previous_state(self):
        first, _, _, logical = self.make_field()
        original = paged_storage._sync_directory
        journal = self.root / "core/paged_write.pending.json"
        failed = False

        def fail_once(path):
            nonlocal failed
            if path == self.root / "core" and not journal.exists() and not failed:
                failed = True
                raise OSError("commit cleanup sync failed")
            return original(path)

        with CoreRuntime(self.root) as core:
            with patch.object(paged_storage, "_sync_directory", fail_once):
                with self.assertRaisesRegex(OSError, "cleanup sync"):
                    core.replace(first, "changed before cleanup")
            self.assertEqual(core.export_state_bytes(), logical)
        with CoreRuntime(self.root) as core:
            self.assertEqual(core.export_state_bytes(), logical)

    def test_failed_second_page_replace_rolls_back_in_memory_and_on_disk(self):
        first, second, _, logical = self.make_field()
        original = paged_storage._atomic_write
        failed = False

        def fail_once(path, payload):
            nonlocal failed
            if path.name.endswith(".meta.json") and not failed:
                failed = True
                raise OSError("one page replacement failed")
            return original(path, payload)

        with CoreRuntime(self.root) as core:
            with patch.object(paged_storage, "_atomic_write", fail_once):
                with self.assertRaisesRegex(OSError, "replacement failed"):
                    core.apply_batch((ReplaceCommand(first, "changed"), ReplaceCommand(second, "changed too")))
            self.assertTrue(core.is_open)
            self.assertEqual(core.export_state_bytes(), logical)
        with CoreRuntime(self.root) as core:
            self.assertEqual(core.export_state_bytes(), logical)
        self.assertFalse((self.root / "core/paged_write.pending.json").exists())

    def test_process_exit_between_page_updates_recovers_old_state(self):
        _, _, _, logical = self.make_field()
        code = '''
import os, sys
from pathlib import Path
from nollm_core import CoreRuntime, GeometryAddress, AtomHandle, ReplaceCommand
from nollm_core import paged_storage
original = paged_storage._atomic_write
def exit_after_body(path, payload):
    original(path, payload)
    if "pages" in path.parts and not path.name.endswith(".meta.json"):
        os._exit(23)
with CoreRuntime(Path(sys.argv[1])) as core:
    paged_storage._atomic_write = exit_after_body
    h = AtomHandle(GeometryAddress("default_dream_v1", "default", -2, 0, 0), "first")
    core.apply_batch((ReplaceCommand(h, "interrupted replacement"),))
'''
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(sys.path)
        result = subprocess.run([sys.executable, "-B", "-c", code, str(self.root)], env=env,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertTrue((self.root / "core/paged_write.pending.json").exists())
        with CoreRuntime(self.root) as core:
            self.assertEqual(core.export_state_bytes(), logical)
        self.assertFalse((self.root / "core/paged_write.pending.json").exists())

    def test_missing_occupancy_metadata_rebuilds_from_existing_pages(self):
        self.make_field()
        with CoreRuntime(self.root) as core:
            expected = core.occupied_cells()
            total = core.layer_content_totals(0)
        for path in (self.root / "core/pages").rglob("*.meta.json"):
            path.unlink()
        with CoreRuntime(self.root) as core:
            self.assertEqual(core.occupied_cells(), expected)
            self.assertEqual(core.layer_content_totals(0), total)

    def test_full_import_keeps_layout_and_replaces_old_pages(self):
        _, _, _, logical = self.make_field()
        with CoreRuntime(self.root) as core:
            core.put(MemoryAtom("extra", "other page"), cell(0, 10000, 0))
            core.import_state_bytes(logical)
            self.assertEqual(core.storage_layout, "paged")
            self.assertEqual(core.export_state_bytes(), logical)
            self.assertEqual(core.atoms_at(cell(0, 10000, 0)), ())
        with CoreRuntime(self.root) as core:
            self.assertEqual(core.export_state_bytes(), logical)

    def test_surface_and_recall_match_before_and_after_migration(self):
        with CoreRuntime(self.root) as core:
            core.put(MemoryAtom("surface", "short"), cell(-2))
            core.put(MemoryAtom("middle", "conditions"), cell(-1))
            core.put(MemoryAtom("detail", "details"), cell())
            scope = PhysicalFieldScope("default_dream_v1", "default", (-2, -1, 0), -2)
            request = CoreRecallRequest("compare", (cell(-2),), ("coverage_down",), RecallBudget(2, 16, 2, 0, 0, 20))
            surface = core.surface_page(scope, 0, None, 8)
            recalled = core.recall(request)
            core.enable_paged_storage(partition_width=4)
            self.assertEqual(core.recall(request), recalled)
        with CoreRuntime(self.root) as core:
            self.assertEqual(core.surface_page(scope, 0, None, 8), surface)
            self.assertEqual(core.recall(request), recalled)


if __name__ == "__main__":
    unittest.main()
