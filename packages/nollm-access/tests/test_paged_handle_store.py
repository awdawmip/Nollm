"""Physical binding pages preserve v2 identities and touch only selected pages."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from nollm_access.handle_store import FileHandleStore, HandleBinding, PAGED_SCHEMA_VERSION
from nollm_core import AtomHandle, GeometryAddress


def handle(identity, q=0, r=0, layer=0):
    return AtomHandle(GeometryAddress("default_dream_v1", "default", layer, q, r), identity)


class PagedHandleStoreTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.store = FileHandleStore(self.root)
        self.first = handle("slot-a")
        self.same_page = handle("slot-b", 1)
        self.far = handle("slot-far", 128)
        self.store.put("a.v1", self.first)
        self.store.put("a.support", self.first)
        self.store.put("b.v1", self.same_page)
        self.store.put("far.v1", self.far)

    def enable(self):
        self.store.enable_paged_storage(partition_width=64)
        return json.loads(self.store.path.read_text())

    def test_explicit_migration_and_v2_export_remain_exact(self):
        before = self.store.state_bytes()
        marker = self.enable()
        self.assertEqual(marker["schema_version"], PAGED_SCHEMA_VERSION)
        self.assertTrue(self.store.is_paged)
        self.assertEqual(self.store.state_bytes(), before)
        reopened = FileHandleStore(self.root)
        self.assertEqual(reopened.get("a.support"), self.first)
        self.assertEqual(reopened.binding_for_handle(self.first).supporting_statement_ids, ("a.support",))
        reopened.import_state(before)
        self.assertEqual(reopened.state_bytes(), before)
        self.assertTrue(reopened.is_paged)
        self.assertEqual(json.loads(before)["schema_version"], "nollm_access_bindings_v2")
        reopened.enable_paged_storage(64)
        with self.assertRaisesRegex(ValueError, "different partition width"):
            reopened.enable_paged_storage(32)

    def test_known_handles_read_each_page_once_without_unrelated_page(self):
        marker = self.enable()
        local_path = self.store._page_path(marker, self.first)
        reads = []
        original = FileHandleStore._read_page

        def selected(store, document, path):
            reads.append(path)
            self.assertEqual(path, local_path)
            return original(store, document, path)

        missing = handle("missing", 2)
        with patch.object(FileHandleStore, "_read_page", selected):
            actual = self.store.bindings_for_handles((self.first, self.same_page, missing))
        self.assertEqual([binding.current_statement_id for binding in actual], ["a.v1", "b.v1"])
        self.assertEqual(reads, [local_path])

    def test_fresh_put_reuse_revision_and_move_do_not_inventory(self):
        self.enable()
        new = handle("new", -65, 2)
        moved = handle("new", 65, 2)
        with patch.object(self.store, "_all_bindings", side_effect=AssertionError("unrelated inventory")):
            self.store.put("new.v1", new, fresh_statement=True)
            self.store.put("new.support", new, fresh_statement=True)
            self.store.move_handle(new, moved)
            binding = self.store.binding_for_handle(moved)
            self.assertEqual(binding.supporting_statement_ids, ("new.support",))
            self.store.revise_current(moved, "new.v2", moved, fresh_statement=True)
            self.assertEqual(self.store.binding_for_handle(moved).current_statement_id, "new.v2")
            self.assertEqual(self.store.binding_for_handle(moved).supporting_statement_ids, ())
            self.store.remove_handle(moved)
        self.assertFalse(self.store.exists("new.v2"))
        self.assertEqual(self.store.get("far.v1"), self.far)

    def test_savepoint_restores_occupied_and_empty_handles_preserving_neighbors(self):
        self.enable()
        empty = handle("new-slot", 130)
        before = self.store.state_bytes()
        snapshot = self.store.export_handle_state((self.first, empty))
        self.store.replace_handles((self.first, empty), (HandleBinding(empty, "a.v1", ("a.support",)),))
        self.assertEqual(self.store.get("a.v1"), empty)
        with patch.object(self.store, "_all_bindings", side_effect=AssertionError("global recovery")):
            self.store.import_handle_state(snapshot)
        self.assertEqual(self.store.state_bytes(), before)
        self.assertEqual(self.store.binding_for_handle(self.same_page).current_statement_id, "b.v1")
        self.assertEqual(self.store.binding_for_handle(self.far).current_statement_id, "far.v1")
        self.assertEqual(self.store.bindings_for_handles((empty,)), ())

    def test_final_scope_rebinding_allows_released_ids_and_rejects_outside_duplicates(self):
        self.enable()
        before = self.store.state_bytes()
        with self.assertRaisesRegex(ValueError, "already bound"):
            self.store.replace_handles((self.first,), (HandleBinding(self.first, "far.v1"),))
        self.assertEqual(self.store.state_bytes(), before)
        with self.assertRaisesRegex(ValueError, "already bound"):
            self.store.put("a.support", self.far)
        with patch.object(self.store, "_all_bindings", side_effect=AssertionError("released local IDs")):
            self.store.replace_handles((self.first, self.same_page),
                                       (HandleBinding(self.first, "b.v1"),
                                        HandleBinding(self.same_page, "a.v1", ("a.support",))))
        self.assertEqual(self.store.get("b.v1"), self.first)
        self.assertEqual(self.store.get("a.support"), self.same_page)

    def test_current_revision_slot_inventory_still_finds_multiple_physical_candidates(self):
        self.enable()
        another = handle("slot-a", -128)
        self.store.put("other.current", another, fresh_statement=True)
        self.store.revise_current(self.first, "a.v2", self.first, fresh_statement=True)
        candidates = self.store.bindings_for_atom_ids(("slot-a",))
        self.assertEqual({binding.current_statement_id for binding in candidates}, {"a.v2", "other.current"})
        self.assertFalse(self.store.exists("a.v1"))

    def test_full_import_failure_keeps_old_visible_pages(self):
        self.enable()
        marker_before = self.store.path.read_bytes()
        before = self.store.state_bytes()
        replacement = FileHandleStore._encode((HandleBinding(handle("replacement", 400), "replacement"),))
        with patch.object(self.store, "_write_page", side_effect=OSError("fixture write failure")):
            with self.assertRaisesRegex(OSError, "fixture write failure"):
                self.store.import_state(replacement)
        self.assertEqual(self.store.path.read_bytes(), marker_before)
        self.assertEqual(self.store.state_bytes(), before)

    def test_empty_scope_and_invalid_import_have_no_effect(self):
        self.enable()
        before = self.store.state_bytes()
        with patch.object(self.store, "_write_page", side_effect=AssertionError("empty scope wrote")):
            self.store.replace_handles((), ())
            self.store.import_handle_state(self.store.export_handle_state(()))
        broken = json.loads(before)
        broken["bindings"].append(broken["bindings"][0])
        with self.assertRaisesRegex(ValueError, "duplicate binding identity"):
            self.store.import_state(json.dumps(broken).encode())
        self.assertEqual(self.store.state_bytes(), before)

    def test_legacy_local_savepoint_and_public_uniqueness_are_compatible(self):
        before = self.store.state_bytes()
        empty = handle("legacy-new", 2)
        snapshot = self.store.export_handle_state((self.first, empty))
        self.store.replace_handles((self.first, empty), (HandleBinding(empty, "a.v1"),))
        self.store.import_handle_state(snapshot)
        self.assertEqual(self.store.state_bytes(), before)
        self.assertEqual(self.store.path.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, "already bound"):
            self.store.put("a.v1", self.far)


if __name__ == "__main__":
    unittest.main()
