"""Functional checks for persisted, current-content formation budgets."""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from nollm_access import (
    AccessDecision, AccessRecallRequest, AccessRuntime, ContentBudgetExceeded,
    ContentBudgetPolicy, EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID,
    FileHandleStore, FileStatementStore, LayerContentBudget, MemoryStatement,
)
from nollm_core import CoreRuntime, GeometryAddress, RecallBudget


def cell(layer=-1, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def decision(identity, action, **kwargs):
    return AccessDecision(
        f"content:{identity}:{action}", identity, action,
        reason_text="Host chose this text and geometry in the functional fixture.",
        decided_by="fixture", write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID,
        **kwargs,
    )


@contextmanager
def opened(root, **kwargs):
    with CoreRuntime(root) as core, AccessRuntime(
        core, FileStatementStore(root), FileHandleStore(root), **kwargs,
    ) as access:
        yield access, core


def put(access, identity, text, at=cell()):
    access.capture(MemoryStatement(identity, text, "fixture:original"))
    return access.apply(decision(identity, "new", target_cell=at))


class ContentBudgetTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(prefix="nollm-content-budget-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def configure(self, **kwargs):
        policy = ContentBudgetPolicy({-1: LayerContentBudget(**kwargs)})
        policy.save(self.root)
        return policy

    def assert_rejected_unchanged(self, access, core, chosen, metric):
        state, bindings = core.export_state_bytes(), access.handle_store.state_bytes()
        with self.assertRaises(ContentBudgetExceeded) as failure:
            access.apply(chosen)
        self.assertEqual(failure.exception.metric, metric)
        self.assertEqual(core.export_state_bytes(), state)
        self.assertEqual(access.handle_store.state_bytes(), bindings)
        self.assertEqual(access.last_commit_state, "pre_commit")
        return failure.exception

    def test_optional_policy_and_persistence(self):
        with opened(self.root) as (access, core):
            self.assertIsNone(access.content_budget)
            put(access, "legacy", "正文" * 30)
            original = core.export_state_bytes()
        policy = self.configure(max_cell_utf8_bytes=12)
        with opened(self.root) as (access, core):
            self.assertEqual(access.content_budget, policy)
            self.assertEqual(core.export_state_bytes(), original)
            result = access.recall(AccessRecallRequest(
                "read-legacy", entry_cells=(cell(),), allowed_kernels=(),
                budget=RecallBudget(0, 4, 0, 0, 0, 4),
            ))
            self.assertEqual(result.items[0].evidence_utf8, "正文" * 30)

    def test_utf8_boundary_is_checked_before_current_mutation(self):
        self.configure(max_cell_utf8_bytes=6)
        with opened(self.root) as (access, core):
            put(access, "at-limit", "短句")
            access.capture(MemoryStatement("over", "a", "fixture:over"))
            failure = self.assert_rejected_unchanged(
                access, core, decision("over", "new", target_cell=cell()), "cell_utf8_bytes",
            )
            self.assertEqual((failure.before, failure.after, failure.limit), (6, 7, 6))
            self.assertTrue(access.statement_store.exists("over"))
            self.assertFalse(access.handle_store.exists("over"))

    def test_short_statements_cannot_overflow_cell_atom_limit(self):
        self.configure(max_cell_atoms=2, max_cell_utf8_bytes=100)
        with opened(self.root) as (access, core):
            put(access, "one", "一")
            put(access, "two", "二")
            access.capture(MemoryStatement("three", "三"))
            self.assert_rejected_unchanged(
                access, core, decision("three", "new", target_cell=cell()), "cell_atoms",
            )

    def test_short_cells_cannot_overflow_declared_surface(self):
        self.configure(max_layer_cells=2)
        with opened(self.root) as (access, core):
            put(access, "one", "一", cell(q=0))
            put(access, "two", "二", cell(q=1))
            access.capture(MemoryStatement("three", "三"))
            self.assert_rejected_unchanged(
                access, core, decision("three", "new", target_cell=cell(q=2)), "layer_cells",
            )
            put(access, "deeper", "具体说明" * 40, cell(layer=0))
            self.assertEqual(core.placement_count(), 3)

    def test_surface_byte_total_is_independent_of_cell_limit(self):
        self.configure(max_cell_utf8_bytes=12, max_layer_utf8_bytes=9)
        with opened(self.root) as (access, core):
            put(access, "one", "短句", cell(q=0))
            put(access, "two", "短", cell(q=1))
            access.capture(MemoryStatement("three", "a"))
            self.assert_rejected_unchanged(
                access, core, decision("three", "new", target_cell=cell(q=2)), "layer_utf8_bytes",
            )

    def test_revision_replaces_bytes_and_preserves_previous_evidence(self):
        self.configure(max_cell_atoms=1, max_cell_utf8_bytes=9, max_layer_utf8_bytes=9)
        with opened(self.root) as (access, core):
            original = put(access, "v1", "短句")
            access.capture(MemoryStatement("v2", "新短句"))
            current = access.apply(decision("v2", "revision_current", existing_handle=original))
            self.assertEqual(core.get(current).payload_utf8, "新短句")
            self.assertEqual(core.placement_count(), 1)
            self.assertEqual(access.statement_store.get("v1").content_utf8, "短句")
            access.capture(MemoryStatement("v3", "第四字句"))
            self.assert_rejected_unchanged(
                access, core, decision("v3", "revision_current", existing_handle=current), "cell_utf8_bytes",
            )
            self.assertEqual(access.handle_store.statement_for_handle(current), "v2")

    def test_support_expression_has_no_current_body_or_atom_increment(self):
        self.configure(max_cell_atoms=1, max_cell_utf8_bytes=6, max_layer_utf8_bytes=6)
        with opened(self.root) as (access, core):
            handle = put(access, "current", "短句")
            before = core.export_state_bytes()
            access.capture(MemoryStatement("support", "完整支持材料" * 100))
            access.apply(decision("support", "reuse", existing_handle=handle))
            self.assertEqual(core.export_state_bytes(), before)
            self.assertEqual(access.handle_store.statement_for_handle(handle), "current")
            self.assertEqual(access.statement_store.get("support").content_utf8, "完整支持材料" * 100)
            # A separate physical history placement is a new current body.
            access.capture(MemoryStatement("retained", "单独物理版本"))
            self.assert_rejected_unchanged(
                access, core, decision("retained", "revision_keep_history", target_cell=cell()), "cell_atoms",
            )

    def test_same_layer_move_counts_removed_source_cell_and_bytes(self):
        self.configure(max_cell_atoms=1, max_layer_cells=2, max_layer_utf8_bytes=6)
        with opened(self.root) as (access, core):
            first = put(access, "one", "一", cell(q=0))
            put(access, "two", "二", cell(q=1))
            moved = access.apply(decision("one", "move", existing_handle=first, target_cell=cell(q=2)))
            self.assertEqual(core.atoms_at(cell(q=0)), ())
            self.assertEqual(core.get(moved).payload_utf8, "一")
            self.assertEqual(len(core.occupied_cells()), 2)
            self.assert_rejected_unchanged(
                access, core, decision("one", "move", existing_handle=moved, target_cell=cell(q=1)), "cell_atoms",
            )

    def test_cross_layer_move_checks_actual_current_body(self):
        self.configure(max_cell_utf8_bytes=6)
        with opened(self.root) as (access, core):
            lower = put(access, "lower", "较长的实际正文", cell(layer=0))
            access.capture(MemoryStatement("short-support", "短"))
            access.apply(decision("short-support", "reuse", existing_handle=lower))
            self.assert_rejected_unchanged(
                access, core,
                decision("short-support", "move", existing_handle=lower, target_cell=cell()),
                "cell_utf8_bytes",
            )
            self.assertEqual(access.saved_handle("lower"), lower)

    def test_old_overfull_content_can_shrink_without_pretending_it_fits(self):
        with opened(self.root) as (access, core):
            handle = put(access, "old", "原有的长正文")
        self.configure(max_cell_utf8_bytes=6, max_layer_utf8_bytes=6)
        with opened(self.root) as (access, core):
            access.capture(MemoryStatement("less", "仍然较长"))
            current = access.apply(decision("less", "revision_current", existing_handle=handle))
            self.assertEqual(core.get(current).payload_utf8, "仍然较长")
            access.capture(MemoryStatement("grow", "再次增长正文"))
            self.assert_rejected_unchanged(
                access, core, decision("grow", "revision_current", existing_handle=current), "cell_utf8_bytes",
            )
            access.capture(MemoryStatement("fit", "短句"))
            current = access.apply(decision("fit", "revision_current", existing_handle=current))
            self.assertEqual(core.get(current).payload_utf8, "短句")
            self.assertTrue(access.statement_store.exists("old"))

    def test_direct_policy_and_malformed_policy_behavior(self):
        policy = ContentBudgetPolicy({-1: LayerContentBudget(max_cell_atoms=0)})
        with opened(self.root, content_budget=policy) as (access, core):
            access.capture(MemoryStatement("blocked", "short"))
            self.assert_rejected_unchanged(
                access, core, decision("blocked", "new", target_cell=cell()), "cell_atoms",
            )
        (self.root / "access" / "content_budget.json").write_text('{"layers": {}}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid content budget"):
            with opened(self.root):
                pass
        with self.assertRaises(ValueError):
            LayerContentBudget(max_cell_atoms=-1)


if __name__ == "__main__":
    unittest.main()
