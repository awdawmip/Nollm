"""Actual native read/write preparation, single entries and observed-path reuse."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from nollm_access import ContentBudgetPolicy, FileStatementStore, LayerContentBudget
from nollm_access.write_policy import EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID
from project_memory import decide, encounter, save_statement


SOURCE = "fixture:encounter-local-cost"


class EncounterLocalCostTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.field = Path(temporary.name) / "field"

    def save(self, name, layer=0, q=0, r=0):
        return save_statement(self.field, name, f"A complete judgment for {name}.", [SOURCE],
                              (q, r), None, layer=layer,
                              write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)

    def enter(self, **options):
        page = encounter(self.field, order=0, page_size=8, steps=0, **options)
        while page["kind"] != "locality":
            page = encounter(self.field, [page["candidates"][0]["id"]], cursor=page["cursor"])
        return page

    def test_single_member_is_explicitly_shown_and_needs_one_host_choice(self):
        self.save("single")
        page = encounter(self.field, order=0, page_size=8, steps=0)
        candidate, = page["candidates"]
        self.assertEqual(candidate["physical_cell"], [0, 0, 0])
        self.assertTrue(candidate["selects_single_physical_entry"])
        local = encounter(self.field, [candidate["id"]], cursor=page["cursor"])
        self.assertEqual(local["kind"], "locality")
        self.assertEqual(local["entry"], [0, 0, 0])
        self.assertEqual([item["id"] for item in local["items"]], ["single"])

    def test_multiple_members_keep_the_physical_choice(self):
        self.save("upper", -1)
        self.save("lower", 0)
        page = encounter(self.field, layers=(-1, 0), order=0, page_size=8, steps=0)
        candidate = next(item for item in page["candidates"] if item["source_cells"] > 1)
        self.assertNotIn("selects_single_physical_entry", candidate)
        physical = encounter(self.field, [candidate["id"]], cursor=page["cursor"])
        self.assertEqual(physical["kind"], "physical")
        self.assertGreater(len(physical["candidates"]), 1)
        chosen = physical["candidates"][-1]
        local = encounter(self.field, [chosen["id"]], cursor=physical["cursor"])
        self.assertEqual(local["entry"], chosen["physical_cell"])

    def test_reading_and_terminal_recall_do_not_prepare_writes(self):
        self.save("read")
        with patch("project_memory.write_pressure", side_effect=AssertionError("pressure during read")), \
             patch("project_memory.incoming_coverage", side_effect=AssertionError("incoming during read")):
            local = self.enter()
            self.assertFalse(local["write_prepared"])
            self.assertEqual(local["cells"], [])
            self.assertTrue(local["descent_candidates"])
            with patch("project_memory.encounter", side_effect=AssertionError("repeated full encounter")):
                selected = decide(self.field, local["cursor"], "recall", "read")
        self.assertEqual(selected["item"]["sources"], [SOURCE])
        self.assertTrue(selected["item"]["current"])

    def test_pressure_is_requested_separately_and_reading_can_resume(self):
        self.save("root", 0, 67, 5)
        local = self.enter(layers=(0, 1), surface_layers=(0,))
        with patch("project_memory.write_pressure", side_effect=AssertionError("unrequested pressure")):
            prepared = encounter(self.field, cursor=local["cursor"], prepare_write=True)
        self.assertTrue(prepared["write_prepared"])
        self.assertTrue(prepared["cells"])
        self.assertTrue(all("write_pressure" not in cell for cell in prepared["cells"]))
        missing = next(cell for cell in prepared["cells"] if cell["cell"] == [1, 94, -30])
        self.assertFalse(missing["readable_downward"])
        self.assertFalse(missing["at_focus"])
        scored = encounter(self.field, cursor=prepared["cursor"], pressure=True)
        self.assertTrue(all("write_pressure" in cell for cell in scored["cells"]))
        with patch("project_memory.write_pressure", side_effect=AssertionError("pressure after read-only")):
            reading = encounter(self.field, cursor=scored["cursor"], prepare_write=False)
        self.assertEqual(reading["cells"], [])
        self.assertFalse(reading["pressure_requested"])
        with self.assertRaisesRegex(ValueError, "read-only"):
            encounter(self.field, cursor=local["cursor"], prepare_write=False, pressure=True)

    def test_new_requires_prepared_candidates_but_revision_uses_read_context(self):
        self.save("old")
        local = self.enter()
        with self.assertRaisesRegex(ValueError, "prepare writing"):
            decide(self.field, local["cursor"], "new", "cell:0:0:0", note_id="new",
                   body="An additional fact", sources=[SOURCE])
        changed = decide(self.field, local["cursor"], "revision", "old", note_id="revised",
                         body="A corrected value", sources=[SOURCE])
        self.assertEqual(changed["revises"], "old")
        with self.assertRaisesRegex(ValueError, "revised"):
            decide(self.field, local["cursor"], "recall", "old")

    def test_observations_accumulate_across_descent_without_body_copies(self):
        self.save("upper", -1)
        self.save("lower", 0)
        local = self.enter(layers=(-1, 0), surface_layers=(-1,))
        prepared = encounter(self.field, cursor=local["cursor"], prepare_write=True)
        lower = encounter(self.field, cursor=prepared["cursor"], descend="cell:0:0:0")
        observations = {item["id"]: item for item in lower["cursor"]["observed_items"]}
        self.assertEqual(set(observations), {"upper", "lower"})
        self.assertEqual(observations["upper"]["focus_path"], [[-1, 0, 0]])
        self.assertEqual(observations["lower"]["focus_path"], [[-1, 0, 0], [0, 0, 0]])
        self.assertIn("handle", observations["upper"])
        self.assertTrue(all("text" not in item for item in observations.values()))
        self.assertTrue(any(item["writable"] for item in lower["cursor"]["observed_cells"]))

    def test_deep_focus_keeps_local_write_window_and_unconfigured_budget_visible(self):
        self.save("entry")
        self.save("deep", 9)
        ContentBudgetPolicy({0: LayerContentBudget(max_cell_atoms=2),
                             9: LayerContentBudget(max_cell_atoms=2)}).save(self.field)
        local = self.enter(layers=tuple(range(11)), surface_layers=(0,), via="downward")
        for layer in range(1, 10):
            local = encounter(self.field, cursor=local["cursor"], descend=f"cell:{layer}:0:0")
        self.assertEqual(local["focus"], [9, 0, 0])
        self.assertEqual(local["local_writable_layers"], [8, 9, 10])
        prepared = encounter(self.field, cursor=local["cursor"], prepare_write=True)
        target = next(cell for cell in prepared["cells"] if cell["cell"] == [10, 0, 0])
        self.assertFalse(target["content_budget_configured"])
        with self.assertRaisesRegex(ValueError, "content budget for layer 10"):
            decide(self.field, prepared["cursor"], "new", target["id"], note_id="unbudgeted",
                   body="A new lower fact", sources=[SOURCE])
        self.assertFalse(FileStatementStore(self.field).exists("unbudgeted"))

    def test_each_recalled_statement_is_read_once_in_locality(self):
        self.save("once")
        local = self.enter()
        reads = []
        original = FileStatementStore.get

        def counted(store, statement_id):
            reads.append(statement_id)
            return original(store, statement_id)

        with patch.object(FileStatementStore, "get", counted):
            encounter(self.field, cursor=local["cursor"])
        self.assertEqual(reads, ["once"])


if __name__ == "__main__":
    unittest.main()
