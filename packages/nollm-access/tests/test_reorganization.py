"""Behavioral checks for final-layout, recoverable local Host reorganization."""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import unittest

from nollm_access import (
    AccessDecision, AccessRuntime, ContentBudgetExceeded, ContentBudgetPolicy,
    EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID, FileHandleStore, FileStatementStore,
    LayerContentBudget, MemoryStatement,
)
from nollm_core import CoreRuntime, GeometryAddress
import nollm_access.runtime as runtime_module


def cell(q=0, layer=-2):
    return GeometryAddress("default_dream_v1", "default", layer, q, 0)


def decision(identity, action, **kwargs):
    return AccessDecision(
        f"reform:{identity}:{action}", identity, action,
        reason_text="The Host selected this local reorganization.", decided_by="fixture",
        write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID, **kwargs,
    )


@contextmanager
def opened(root):
    with CoreRuntime(root) as core, AccessRuntime(
        core, FileStatementStore(root), FileHandleStore(root),
    ) as access:
        yield access, core


def put(access, identity, text, at=cell()):
    access.capture(MemoryStatement(identity, text, "fixture:source"))
    return access.apply(decision(identity, "new", target_cell=at))


class ReorganizationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="nollm-reorganization-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def configure(self, **kwargs):
        policy = ContentBudgetPolicy({-2: LayerContentBudget(**kwargs)})
        policy.save(self.root)
        return policy

    def test_grow_then_shrink_checks_final_bytes_and_preserves_history(self):
        self.configure(max_cell_atoms=2, max_cell_utf8_bytes=6, max_layer_utf8_bytes=6)
        with opened(self.root) as (access, core):
            first = put(access, "first.v1", "A")
            second = put(access, "second.v1", "BBBBB")
            original = access.statement_store.get("first.v1")
            newer = (MemoryStatement("first.v2", "AAA"), MemoryStatement("second.v2", "BB"))
            with patch.object(core, "export_state_bytes", side_effect=AssertionError("whole Core backup")):
                result = access.reorganize((
                    decision("first.v2", "revision_current", existing_handle=first),
                    decision("second.v2", "revision_current", existing_handle=second),
                ), statements=newer)
            self.assertEqual(result, (first, second))
            self.assertEqual(core.get(first).payload_utf8, "AAA")
            self.assertEqual(core.get(second).payload_utf8, "BB")
            self.assertEqual(access.handle_store.statement_for_handle(first), "first.v2")
            self.assertEqual(access.statement_store.get("first.v1"), original)
            self.assertEqual(access.last_commit_state, "committed")

    def test_replace_full_cell_by_adding_before_retiring_old_occupancy(self):
        self.configure(max_cell_atoms=1, max_layer_cells=1)
        with opened(self.root) as (access, core):
            old = put(access, "old", "old interpretation")
            result = access.reorganize((
                decision("new", "new", target_cell=cell()),
                decision("old", "forget", existing_handle=old),
            ), statements=(MemoryStatement("new", "short interpretation"),))
            self.assertEqual(core.placement_count(), 1)
            self.assertEqual(core.get(result[0]).payload_utf8, "short interpretation")
            self.assertFalse(access.handle_store.exists("old"))
            self.assertEqual(access.statement_store.get("old").content_utf8, "old interpretation")

    def test_paged_swap_between_two_full_cells_keeps_supports(self):
        self.configure(max_cell_atoms=1, max_layer_cells=2)
        with opened(self.root) as (access, core):
            a = put(access, "a", "A", cell(0))
            b = put(access, "b", "B", cell(128))
            access.capture(MemoryStatement("a.support", "additional source"))
            access.apply(decision("a.support", "reuse", existing_handle=a))
            core.enable_paged_storage(partition_width=64)
            access.handle_store.enable_paged_storage(partition_width=64)
            moved_a, moved_b = access.reorganize((
                decision("a", "move", existing_handle=a, target_cell=cell(128)),
                decision("b", "move", existing_handle=b, target_cell=cell(0)),
            ))
            self.assertEqual(core.get(moved_a).payload_utf8, "A")
            self.assertEqual(core.get(moved_b).payload_utf8, "B")
            self.assertEqual(access.handle_store.get("a.support"), moved_a)
            self.assertEqual(core.layer_content_totals(-2), (2, 2))
        with opened(self.root) as (access, core):
            self.assertEqual(access.handle_store.get("a").geometry_address, cell(128))
            self.assertEqual(core.get(access.handle_store.get("b")).payload_utf8, "B")

    def test_final_overflow_rejects_before_capture_or_state_changes(self):
        self.configure(max_cell_atoms=1)
        with opened(self.root) as (access, core):
            put(access, "old", "original")
            before, bindings = core.export_state_bytes(), access.handle_store.state_bytes()
            with self.assertRaises(ContentBudgetExceeded):
                access.reorganize((decision("extra", "new", target_cell=cell()),),
                                  statements=(MemoryStatement("extra", "extra"),))
            self.assertEqual(core.export_state_bytes(), before)
            self.assertEqual(access.handle_store.state_bytes(), bindings)
            self.assertFalse(access.statement_store.exists("extra"))
            self.assertFalse((self.root / "access/reorganization.pending.json").exists())

    def test_id_bound_outside_local_scope_is_rejected_before_changes(self):
        with opened(self.root) as (access, core):
            put(access, "remote", "already bound", cell(512))
            before = core.export_state_bytes()
            with self.assertRaisesRegex(ValueError, "already bound"):
                access.reorganize((decision("remote", "new", target_cell=cell()),))
            self.assertEqual(core.export_state_bytes(), before)

    def test_conflicting_new_bindings_do_not_capture_partial_inputs(self):
        with opened(self.root) as (access, core):
            with self.assertRaisesRegex(ValueError, "already bound"):
                access.reorganize((
                    decision("same", "new", target_cell=cell()),
                    decision("same", "new", target_cell=cell(1)),
                ), statements=(MemoryStatement("same", "body"),))
            self.assertEqual(core.placement_count(), 0)
            self.assertFalse(access.statement_store.exists("same"))

    def test_binding_failure_restores_current_state_but_keeps_captured_evidence(self):
        with opened(self.root) as (access, core):
            handle = put(access, "v1", "old")
            before, bindings = core.export_state_bytes(), access.handle_store.state_bytes()
            original_replace = access.handle_store.replace_handles
            first_call = True

            def fail_after_replace(*args, **kwargs):
                nonlocal first_call
                original_replace(*args, **kwargs)
                if first_call:
                    first_call = False
                    raise OSError("failed after replacing bindings")

            with patch.object(access.handle_store, "replace_handles", side_effect=fail_after_replace):
                with self.assertRaisesRegex(OSError, "replacing bindings"):
                    access.reorganize((decision("v2", "revision_current", existing_handle=handle),),
                                      statements=(MemoryStatement("v2", "new"),))
            self.assertEqual(core.export_state_bytes(), before)
            self.assertEqual(access.handle_store.state_bytes(), bindings)
            self.assertEqual(access.statement_store.get("v2").content_utf8, "new")
            self.assertEqual(access.last_commit_state, "rolled_back_failure")
            self.assertFalse((self.root / "access/reorganization.pending.json").exists())

    def test_interruption_restores_cells_bindings_budget_and_configuration_on_open(self):
        old_budget = self.configure(max_cell_atoms=1, max_cell_utf8_bytes=10)
        configuration = self.root / "access/encounter.json"
        configuration.write_text('{"surface_layers":[-2]}\n', encoding="utf-8")
        original_config = configuration.read_bytes()
        with opened(self.root) as (access, core):
            handle = put(access, "v1", "old")
            core.enable_paged_storage(partition_width=64)
            access.handle_store.enable_paged_storage(partition_width=64)
            before, bindings = core.export_state_bytes(), access.handle_store.state_bytes()
            real_write = runtime_module._atomic_write

            def interrupt_after_setting(path, payload):
                real_write(path, payload)
                if path.name == "content_budget.json":
                    raise SystemExit("interrupted after configuration update")

            new_budget = ContentBudgetPolicy({-2: LayerContentBudget(max_cell_atoms=2)})
            with patch.object(runtime_module, "_atomic_write", side_effect=interrupt_after_setting):
                with self.assertRaises(SystemExit):
                    access.reorganize((decision("v2", "revision_current", existing_handle=handle),),
                                      statements=(MemoryStatement("v2", "new"),), content_budget=new_budget,
                                      configuration_files={Path("access/encounter.json"): b'{"surface_layers":[-3]}\n'})
            self.assertTrue((self.root / "access/reorganization.pending.json").exists())
            self.assertEqual(access.lifecycle_state, "FAILED")
        with opened(self.root) as (access, core):
            self.assertEqual(core.export_state_bytes(), before)
            self.assertEqual(access.handle_store.state_bytes(), bindings)
            self.assertEqual(access.content_budget, old_budget)
            self.assertEqual(configuration.read_bytes(), original_config)
            self.assertEqual(access.statement_store.get("v2").content_utf8, "new")
            self.assertFalse((self.root / "access/reorganization.pending.json").exists())

    def test_expansion_settings_and_new_layer_budget_commit_with_content(self):
        self.configure(max_cell_atoms=1, max_layer_cells=1)
        with opened(self.root) as (access, core):
            upper = put(access, "upper.v1", "initial")
            expanded = ContentBudgetPolicy({
                -2: LayerContentBudget(max_cell_atoms=1, max_layer_cells=1),
                -1: LayerContentBudget(max_cell_atoms=1, max_cell_utf8_bytes=128),
            })
            result = access.reorganize((
                decision("upper.v2", "revision_current", existing_handle=upper),
                decision("detail", "new", target_cell=cell(layer=-1)),
            ), statements=(MemoryStatement("upper.v2", "short"), MemoryStatement("detail", "conditions and detail")),
                content_budget=expanded,
                configuration_files={Path("access/encounter.json"): b'{"layers":[-2,-1],"surface_layers":[-2]}\n'})
            self.assertEqual(core.get(result[1]).payload_utf8, "conditions and detail")
            self.assertEqual(access.content_budget, expanded)
        with opened(self.root) as (access, core):
            self.assertEqual(access.content_budget, expanded)
            self.assertEqual(json.loads((self.root / "access/encounter.json").read_text())["layers"], [-2, -1])
            self.assertEqual(access.handle_store.statement_for_handle(upper), "upper.v2")

    def test_support_only_batch_leaves_core_bytes_unchanged(self):
        with opened(self.root) as (access, core):
            handle = put(access, "current", "fact")
            before = core.export_state_bytes()
            result = access.reorganize((decision("support", "reuse", existing_handle=handle),),
                                      statements=(MemoryStatement("support", "new supporting evidence"),))
            self.assertEqual(result, (handle,))
            self.assertEqual(core.export_state_bytes(), before)
            self.assertEqual(access.handle_store.get("support"), handle)
            self.assertEqual(access.handle_store.statement_for_handle(handle), "current")

    def test_ordinary_apply_uses_local_recovery_for_current_changes(self):
        with opened(self.root) as (access, core):
            core.enable_paged_storage(partition_width=64)
            access.handle_store.enable_paged_storage(partition_width=64)
            access.capture(MemoryStatement("v1", "original"))
            access.capture(MemoryStatement("v2", "revised"))
            with patch.object(core, "export_state_bytes", side_effect=AssertionError("whole Core snapshot")), \
                    patch.object(access.handle_store, "state_bytes", side_effect=AssertionError("whole binding snapshot")):
                handle = access.apply(decision("v1", "new", target_cell=cell()))
                access.apply(decision("v2", "revision_current", existing_handle=handle))
                moved = access.apply(decision("v2", "move", existing_handle=handle, target_cell=cell(128)))
                self.assertEqual(core.get(moved).payload_utf8, "revised")
                removed = access.apply(decision("v2", "forget", existing_handle=moved))
            self.assertEqual(removed.payload_utf8, "revised")
            self.assertEqual(core.placement_count(), 0)
            self.assertEqual(access.statement_store.get("v1").content_utf8, "original")

    def test_separate_capture_does_not_skip_a_later_shared_writer_binding(self):
        with opened(self.root) as (first, core):
            second = AccessRuntime(core, FileStatementStore(self.root), FileHandleStore(self.root))
            self.addCleanup(second.close)
            first.capture(MemoryStatement("shared", "fact"))
            second.apply(decision("shared", "new", target_cell=cell(128)))
            with self.assertRaisesRegex(ValueError, "already bound"):
                first.apply(decision("shared", "new", target_cell=cell()))
            self.assertEqual(core.placement_count(), 1)
            self.assertEqual(first.handle_store.get("shared").geometry_address, cell(128))


if __name__ == "__main__":
    unittest.main()
