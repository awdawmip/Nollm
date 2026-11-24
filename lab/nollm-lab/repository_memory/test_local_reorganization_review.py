"""Independent native scenarios for the local-reorganization user flow."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from nollm_access import (
    ContentBudgetPolicy, EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID,
    FileHandleStore, FileStatementStore, LayerContentBudget,
)
from nollm_core import CoreRuntime, expand_physical_coverage
from coverage_cli import address
from local_reorganization import SCHEMA_VERSION, reorganize
from project_memory import describe, encounter, main, save_statement


SOURCE = "fixture:independent-local-reorganization-source"


class LocalReorganizationReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.field = self.root / "field"

    def seed(self, *, root=(-2, 0, 0), children=True):
        save_statement(self.field, "surface.v1", "原文可回溯。", [SOURCE], root[1:], None,
                       layer=root[0], write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
        if children:
            save_statement(self.field, "middle.v1", "条件和事实分层保存。", [SOURCE], (0, 0), None,
                           layer=-1, write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
            save_statement(self.field, "detail.v1", "原始详细表达保持固定来源。", [SOURCE], (0, 0), None,
                           layer=0, write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
        ContentBudgetPolicy({
            -3: LayerContentBudget(max_cell_atoms=1, max_cell_utf8_bytes=64),
            -2: LayerContentBudget(max_cell_atoms=1, max_cell_utf8_bytes=32, max_layer_cells=1, max_layer_utf8_bytes=32),
            -1: LayerContentBudget(max_cell_atoms=1, max_cell_utf8_bytes=128),
            0: LayerContentBudget(max_cell_atoms=1, max_cell_utf8_bytes=512),
        }).save(self.field)
        defaults = {"surface_layers": [-2], "layers": [-3, -2, -1, 0], "order": 0,
                    "page_size": 8, "steps": 0, "limit": 20, "beam": 16,
                    "via": "downward", "compact": True}
        (self.field / "access/encounter.json").write_text(json.dumps(defaults), encoding="utf-8")
        with CoreRuntime(self.field) as core:
            core.enable_paged_storage(partition_width=8)
        FileHandleStore(self.field).enable_paged_storage(partition_width=8)

    def observe(self):
        page = encounter(self.field, prepare_write=True)
        while page["kind"] != "locality":
            candidate, = page["candidates"]
            page = encounter(self.field, [candidate["id"]], cursor=page["cursor"])
        return page

    def observe_detail(self):
        root = self.observe()
        middle = encounter(self.field, cursor=root["cursor"], descend="cell:-1:0:0")
        detail = encounter(self.field, cursor=middle["cursor"], descend="cell:0:0:0")
        return root, middle, detail

    def reform_plan(self, middle):
        candidate = next(item for item in middle["cells"]
                         if item["cell"][0] == 0 and item["cell"] != [0, 0, 0]
                         and item["readable_downward"] and item["native_atoms"] == 0)
        return {
            "schema_version": SCHEMA_VERSION,
            "changes": [
                {"action": "new", "target": "cell:-2:0:0", "id": "surface.v2",
                 "text": "位置可改，原文保留。", "sources": [SOURCE]},
                {"action": "forget", "target": "surface.v1"},
                {"action": "revise", "target": "middle.v1", "id": "middle.v2",
                 "text": "下层原文可以换位，按新路径继续读取。", "sources": [SOURCE]},
                {"action": "move", "target": "detail.v1", "to": candidate["id"]},
            ],
            "readback": [{"id": "detail.v1", "path": [[-2, 0, 0], [-1, 0, 0], candidate["cell"]]}],
        }

    def test_full_surface_reform_and_move_preserve_all_original_versions(self):
        self.seed()
        original = {identity: describe(self.field, identity) for identity in ("surface.v1", "middle.v1", "detail.v1")}
        _, middle, detail = self.observe_detail()
        result = reorganize(self.field, detail["cursor"], self.reform_plan(middle))
        self.assertEqual(result["commit_state"], "committed")
        self.assertEqual({item["id"] for item in result["readback"]}, {"surface.v2", "middle.v2", "detail.v1"})
        for identity, before in original.items():
            after = describe(self.field, identity)
            self.assertEqual(after["text"], before["text"])
            self.assertEqual(after["sources"], before["sources"])
        self.assertFalse(describe(self.field, "surface.v1")["current"])
        self.assertFalse(describe(self.field, "middle.v1")["current"])
        self.assertTrue(describe(self.field, "detail.v1")["current"])
        reopened = self.observe()
        self.assertEqual([item["id"] for item in reopened["items"]], ["surface.v2"])
        reopened = encounter(self.field, cursor=reopened["cursor"], descend="cell:-1:0:0")
        self.assertEqual([item["id"] for item in reopened["items"]], ["middle.v2"])
        path = next(item["path"] for item in result["readback"] if item["id"] == "detail.v1")
        target = "cell:" + ":".join(map(str, path[-1]))
        reopened = encounter(self.field, cursor=reopened["cursor"], descend=target)
        self.assertEqual([item["id"] for item in reopened["items"]], ["detail.v1"])

    def test_real_support_only_candidate_cannot_claim_downward_readback(self):
        self.seed(root=(-2, 0, -2), children=False)
        page = self.observe()
        target = "cell:-1:-2:-2"
        candidate = next(item for item in page["cells"] if item["id"] == target)
        self.assertFalse(candidate["readable_downward"])
        with CoreRuntime(self.field) as core:
            before = core.export_state_bytes()
        for explicit in (False, True):
            with self.subTest(explicit=explicit):
                plan = {"schema_version": SCHEMA_VERSION, "changes": [{
                    "action": "new", "target": target, "id": "unsupported.v1",
                    "text": "这条表达不能从所选入口向下读到。", "sources": [SOURCE]}]}
                if explicit:
                    plan["readback"] = [{"id": "unsupported.v1", "path": [[-2, 0, -2], [-1, -2, -2]]}]
                with self.assertRaisesRegex(ValueError, "forward path|coverage_down"):
                    reorganize(self.field, page["cursor"], plan)
                with CoreRuntime(self.field) as core:
                    self.assertEqual(core.export_state_bytes(), before)
                self.assertFalse(FileStatementStore(self.field).exists("unsupported.v1"))

    def test_move_infers_earlier_forward_path_after_visiting_sibling(self):
        self.seed()
        _, middle, detail = self.observe_detail()
        plan = self.reform_plan(middle)
        del plan["readback"]
        result = reorganize(self.field, detail["cursor"], plan)
        moved = next(item for item in result["readback"] if item["id"] == "detail.v1")
        self.assertEqual(moved["path"][:2], [[-2, 0, 0], [-1, 0, 0]])

    def test_unrelated_revised_observation_does_not_block_current_detail_change(self):
        self.seed()
        _, _, detail = self.observe_detail()
        save_statement(self.field, "surface.other", "入口表述已更新。", [SOURCE], None, "surface.v1",
                       write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
        plan = {"schema_version": SCHEMA_VERSION, "changes": [{
            "action": "revise", "target": "detail.v1", "id": "detail.v2",
            "text": "细节更新，来源与其他布局保留。", "sources": [SOURCE]}]}
        result = reorganize(self.field, detail["cursor"], plan)
        self.assertEqual(result["readback"][0]["id"], "detail.v2")
        self.assertTrue(describe(self.field, "surface.other")["current"])

    def test_new_coarser_surface_and_budget_change_commit_together(self):
        self.seed()
        _, _, detail = self.observe_detail()
        expected_cell = address(-3, 0, 0)
        self.assertIn(address(-2, 0, 0), {item.target for item in expand_physical_coverage(expected_cell, "coverage_down").members})
        policy = ContentBudgetPolicy({
            -3: LayerContentBudget(max_cell_atoms=1, max_cell_utf8_bytes=64, max_layer_cells=1, max_layer_utf8_bytes=64),
            -2: LayerContentBudget(max_cell_atoms=1, max_cell_utf8_bytes=64),
            -1: LayerContentBudget(max_cell_atoms=1, max_cell_utf8_bytes=128),
            0: LayerContentBudget(max_cell_atoms=1, max_cell_utf8_bytes=512),
        })
        plan = {"schema_version": SCHEMA_VERSION, "changes": [{
            "action": "new", "target": "cell:-3:0:0", "id": "coarser.v1",
            "text": "原文、条件与入口逐层展开。", "sources": [SOURCE]}],
            "encounter": {"surface_layers": [-3]}, "content_budget": policy.to_mapping(),
            "readback": [{"id": "detail.v1", "path": [[-3, 0, 0], [-2, 0, 0], [-1, 0, 0], [0, 0, 0]]}]}
        result = reorganize(self.field, detail["cursor"], plan)
        self.assertTrue(result["configuration_updated"])
        self.assertEqual(ContentBudgetPolicy.load(self.field), policy)
        page = self.observe()
        self.assertEqual(page["entry"], [-3, 0, 0])
        self.assertEqual(page["items"][0]["id"], "coarser.v1")
        for target, identity in (("cell:-2:0:0", "surface.v1"), ("cell:-1:0:0", "middle.v1"), ("cell:0:0:0", "detail.v1")):
            page = encounter(self.field, cursor=page["cursor"], descend=target)
            self.assertEqual(page["items"][0]["id"], identity)

    def test_failed_cli_batch_keeps_cursor_and_captured_evidence_for_retry(self):
        self.seed()
        _, middle, detail = self.observe_detail()
        plan = self.reform_plan(middle)
        plan["encounter"] = {"page_size": 4}
        cursor_path, plan_path = self.root / "session.json", self.root / "plan.json"
        cursor_path.write_text(json.dumps(detail["cursor"]), encoding="utf-8")
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        cursor_before = cursor_path.read_bytes()
        configuration_before = (self.field / "access/encounter.json").read_bytes()
        with CoreRuntime(self.field) as core:
            before = core.export_state_bytes()
        original = FileHandleStore.replace_handles
        failed = False

        def fail_once(store, *args, **kwargs):
            nonlocal failed
            if not failed:
                failed = True
                raise OSError("independent binding-write failure")
            return original(store, *args, **kwargs)

        argv = ["--field", str(self.field), "encounter", "--cursor-file", str(cursor_path), "--reorganize", str(plan_path)]
        with patch.object(FileHandleStore, "replace_handles", fail_once), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(OSError, "binding-write failure"):
                main(argv)
        self.assertEqual(cursor_path.read_bytes(), cursor_before)
        self.assertEqual((self.field / "access/encounter.json").read_bytes(), configuration_before)
        with CoreRuntime(self.field) as core:
            self.assertEqual(core.export_state_bytes(), before)
        self.assertTrue(FileStatementStore(self.field).exists("surface.v2"))
        self.assertTrue(FileStatementStore(self.field).exists("middle.v2"))
        with redirect_stdout(io.StringIO()) as output:
            main(argv)
        self.assertEqual(json.loads(output.getvalue())["commit_state"], "committed")
        self.assertFalse(cursor_path.exists())


if __name__ == "__main__":
    unittest.main()
