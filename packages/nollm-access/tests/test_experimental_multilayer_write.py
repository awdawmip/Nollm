"""Actual Access writes under an explicit multilayer experimental policy.

Run with stdlib unittest; pytest can collect the same TestCase classes.
"""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from nollm_access import (
    AccessDecision, AccessRecallRequest, AccessRuntime, FileHandleStore,
    FileStatementStore, MemoryStatement,
)
from nollm_access.write_policy import (
    ACTIVE_SEMANTIC_WRITE_POLICY_ID, ACTIVE_WRITABLE_HEX_RADIUS,
    EXPERIMENTAL_MULTILAYER_WRITE_POLICY,
    EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID,
    ActiveSemanticWritePolicyError, semantic_write_policy,
)
from nollm_core import CoreRuntime, GeometryAddress, RecallBudget


def cell(layer, q=0, r=0):
    return GeometryAddress("default_dream_v1", "default", layer, q, r)


def decision(statement_id, action, *, policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID,
             **values):
    return AccessDecision(
        f"experiment:{action}:{statement_id}", statement_id, action,
        reason_text="The fixture Host explicitly chose this experimental placement.",
        decided_by="fixture", write_policy_id=policy_id, **values,
    )


@contextmanager
def open_field(root):
    with CoreRuntime(root) as core, AccessRuntime(
        core, FileStatementStore(root), FileHandleStore(root),
    ) as access:
        yield access, core


def write(access, statement_id, at, text=None):
    access.put_statement(MemoryStatement(
        statement_id, text or statement_id, f"fixture:source/{statement_id}",
    ))
    return access.apply(decision(statement_id, "new", target_cell=at))


class ExperimentalMultilayerWriteTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="nollm-multilayer-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def test_default_decision_keeps_layer_zero_policy(self):
        chosen = AccessDecision(
            "default", "source", "new", target_cell=cell(0),
            reason_text="Default placement remains on L0.",
        )
        self.assertEqual(chosen.write_policy_id, ACTIVE_SEMANTIC_WRITE_POLICY_ID)
        for layer in (-1, 1):
            with self.subTest(layer=layer), self.assertRaises(ActiveSemanticWritePolicyError) as caught:
                AccessDecision(
                    "default", "source", "new", target_cell=cell(layer),
                    reason_text="No experimental policy was selected.",
                )
            self.assertEqual(caught.exception.policy_id, ACTIVE_SEMANTIC_WRITE_POLICY_ID)
            self.assertEqual(caught.exception.field, "layer")

    def test_experimental_scope_uses_existing_layer_and_radius_domain(self):
        policy = semantic_write_policy(EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
        self.assertIs(policy, EXPERIMENTAL_MULTILAYER_WRITE_POLICY)
        for layer in (-64, -1, 0, 1, 64):
            for q in (-ACTIVE_WRITABLE_HEX_RADIUS, ACTIVE_WRITABLE_HEX_RADIUS):
                address = cell(layer, q)
                with self.subTest(layer=layer, q=q):
                    self.assertEqual(policy.validate(address), address)
                    self.assertEqual(decision("bounded", "new", target_cell=address).target_cell, address)
        with self.assertRaises(ActiveSemanticWritePolicyError) as caught:
            decision("outside", "new", target_cell=cell(1, ACTIVE_WRITABLE_HEX_RADIUS + 1))
        self.assertEqual(caught.exception.policy_id, EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
        self.assertEqual(caught.exception.field, "hex_radius")
        for layer in (-65, 65):
            with self.subTest(layer=layer), self.assertRaises(ValueError):
                cell(layer)

    def test_unknown_policy_is_not_an_implicit_multilayer_mode(self):
        with self.assertRaisesRegex(ValueError, "unknown semantic write policy"):
            decision("unknown", "new", target_cell=cell(1), policy_id="unknown")

    def test_write_reopen_and_single_entry_coverage_recall(self):
        with open_field(self.root) as (access, core):
            write(access, "upper", cell(0), "Upper interpretation")
            write(access, "lower", cell(1), "Lower evidence-backed material")
            self.assertEqual(core.placement_count(), 2)
            self.assertEqual(core.bridges(), ())
            persisted = core.export_state_bytes()

        with open_field(self.root) as (access, core):
            self.assertEqual(core.export_state_bytes(), persisted)
            result = access.recall(AccessRecallRequest(
                "multilayer-native", entry_cells=(cell(0),),
                allowed_kernels=("coverage_down",),
                budget=RecallBudget(1, 16, 1, 0, 0, 16),
            ))
            found = {hit.statement_id: hit for hit in result.items}
            self.assertEqual(set(found), {"upper", "lower"})
            self.assertEqual(found["lower"].evidence_utf8, "Lower evidence-backed material")
            self.assertIsNone(found["lower"].fallback_error)
            self.assertIn("coverage_down", found["lower"].path)
            self.assertEqual(access.statement_store.get("lower").source_handle, "fixture:source/lower")
            self.assertEqual(core.bridges(), ())

    def test_reuse_and_revision_do_not_add_lower_atoms(self):
        with open_field(self.root) as (access, core):
            handle = write(access, "lower-v1", cell(1), "First value")
            initial = core.export_state_bytes()
            access.put_statement(MemoryStatement("expression", "Supporting expression", "fixture:expression"))
            reused = access.apply(decision("expression", "reuse", existing_handle=handle))
            self.assertEqual(reused, handle)
            self.assertEqual(core.export_state_bytes(), initial)
            self.assertEqual(core.placement_count(), 1)
            self.assertEqual(access.handle_store.binding_for_handle(handle).supporting_statement_ids, ("expression",))

            access.put_statement(MemoryStatement("lower-v2", "Revised value", "fixture:revised"))
            revised = access.apply(decision("lower-v2", "revision_current", existing_handle=handle))
            self.assertEqual(revised, handle)
            self.assertEqual(core.placement_count(), 1)
            self.assertEqual(core.get(handle).payload_utf8, "Revised value")
            self.assertEqual(access.handle_store.statement_for_handle(handle), "lower-v2")
            self.assertEqual(access.statement_store.get("lower-v1").content_utf8, "First value")
            self.assertFalse(access.handle_store.exists("lower-v1"))

        with open_field(self.root) as (access, core):
            self.assertEqual(core.placement_count(), 1)
            self.assertEqual(access.saved_handle("lower-v2"), handle)
            self.assertEqual(core.get(handle).payload_utf8, "Revised value")

    def test_default_revision_rejection_preserves_lower_state(self):
        with open_field(self.root) as (access, core):
            handle = write(access, "lower", cell(1))
            before = core.export_state_bytes()
            with self.assertRaises(ActiveSemanticWritePolicyError):
                decision("revision", "revision_current", existing_handle=handle,
                         policy_id=ACTIVE_SEMANTIC_WRITE_POLICY_ID)
            self.assertEqual(core.export_state_bytes(), before)
            self.assertEqual(access.handle_store.statement_for_handle(handle), "lower")

    def test_move_between_layers_preserves_current_and_supporting_bindings(self):
        with open_field(self.root) as (access, core):
            original = write(access, "movable", cell(1), "Material to relocate")
            access.put_statement(MemoryStatement("alias", "Another expression", "fixture:alias"))
            access.apply(decision("alias", "reuse", existing_handle=original))
            moved = access.apply(decision(
                "movable", "move", existing_handle=original, target_cell=cell(2, -1, 1),
            ))
            self.assertEqual(core.atoms_at(cell(1)), ())
            self.assertEqual(core.placement_count(), 1)
            self.assertEqual(access.saved_handle("movable"), moved)
            self.assertEqual(access.saved_handle("alias"), moved)
            self.assertEqual(core.get(moved).payload_utf8, "Material to relocate")
            self.assertEqual(core.bridges(), ())

        with open_field(self.root) as (access, core):
            self.assertEqual(access.saved_handle("movable"), moved)
            self.assertEqual(access.saved_handle("alias"), moved)
            self.assertEqual(core.get(moved).payload_utf8, "Material to relocate")

    def test_policy_does_not_waive_original_evidence_requirement(self):
        with open_field(self.root) as (access, core):
            before = core.export_state_bytes()
            with self.assertRaises(FileNotFoundError):
                access.apply(decision("absent", "new", target_cell=cell(1)))
            self.assertEqual(core.export_state_bytes(), before)
            self.assertEqual(core.placement_count(), 0)


if __name__ == "__main__":
    unittest.main()
