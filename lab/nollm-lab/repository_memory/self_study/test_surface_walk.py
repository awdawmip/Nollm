import tempfile
import unittest
from pathlib import Path

from surface_walk import audit_windows, compare_from_entry, walk

from nollm_access import AccessDecision, AccessRuntime, FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress, PhysicalFieldScope, Q16_ONE


class SurfaceWalkTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.field = Path(temporary.name)
        self.scope = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)
        with CoreRuntime(self.field) as core, AccessRuntime(
            core, FileStatementStore(self.field), FileHandleStore(self.field)
        ) as access:
            for q, r, name in [(0, 0, "recall"), (1, 0, "surface"), (0, 1, "state")]:
                address = GeometryAddress("default_dream_v1", "default", 0, q, r)
                access.put_statement(MemoryStatement(name, f"Read {name}", f"rev:{name}.py"))
                access.apply(AccessDecision("place-" + name, name, "new", address,
                                            decided_by="host", reason_text="Surface test."))

    def test_orders_share_a_native_entry_without_duplicating_mass(self):
        audit = audit_windows(self.field, self.scope, 2)
        self.assertEqual([3 * Q16_ONE] * 3, [row["mass_q16"] for row in audit["orders"]])
        witness = audit["shared_witness"]
        self.assertGreaterEqual(len(witness["order_one_windows"]), 2)
        self.assertEqual(sum(item["up_membership_q16"] for item in witness["order_one_windows"]), Q16_ONE)
        self.assertTrue(witness["current_source_refs_at_cell"])

    def test_one_shown_entry_after_pagination_and_bounded_calls(self):
        result = walk(self.field, self.scope, 2, (1,), page_size=1)
        self.assertEqual([2, 2, 1, 0], [page["shown"][0][0] for page in result["shown_pages"][:-1]])
        self.assertTrue(result["shown_pages"][0]["has_more"])
        self.assertEqual(result["physical_entry"], result["shown_pages"][-1]["opened"])
        direct = [item for item in result["recalled"] if not item["path"]]
        self.assertEqual(len(direct), 1)
        comparison = compare_from_entry(self.field, self.scope, result["physical_entry"])
        for items in comparison["runs"].values():
            self.assertEqual(items[0]["source"], direct[0]["source"])
        self.assertTrue(any(item["path"] == ["lateral"] for item in comparison["runs"]["lateral"]))
        self.assertTrue(any(len(item["path"]) == 2 for item in comparison["runs"]["vertical"]))
        self.assertIsNotNone(direct[0]["source"])
        with self.assertRaisesRegex(RuntimeError, "call limit"):
            walk(self.field, self.scope, 2, (1,), page_size=1, max_calls=3)
        with self.assertRaisesRegex(ValueError, "rank exceeds"):
            walk(self.field, self.scope, 1, (99,), page_size=2)
