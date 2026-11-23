"""Stored upper judgments, separate write scopes and one rooted descent path."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from install_skill import install
from nollm_access import EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID, FileStatementStore
from nollm_core import CoreRuntime
from project_memory import decide, describe, encounter, save_statement


SOURCE = "fixture:stored-surface-source"


class StoredSurfaceEncounterTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.field = self.root / "field"
        for identity, layer, body in (
            ("surface", -2, "支撑不足提高压力；写入仍由 Host 决定。"),
            ("conditions", -1, "压力建议和正文容量分别计算；各覆盖目标共享下层材料。"),
            ("evidence", 0, "完整例证、推导与固定来源。"),
            ("coarser", -3, "更粗的另一层内容。"),
        ):
            save_statement(self.field, identity, body, [SOURCE], (0, 0), None, layer=layer,
                           write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)

    def observe(self, **options):
        page = encounter(self.field, surface_layers=(-2,), layers=(-2, -1, 0),
                         via="downward", steps=0, order=0, page_size=8, **options)
        while page["kind"] != "locality":
            candidate, = page["candidates"]
            page = encounter(self.field, [candidate["id"]], cursor=page["cursor"])
        return page

    def test_surface_reads_only_stored_upper_body_and_descent_reads_next_focus(self):
        reads = []
        original_get = FileStatementStore.get

        def tracked_get(store, identity):
            reads.append(identity)
            return original_get(store, identity)

        with patch.object(FileStatementStore, "get", tracked_get):
            root = self.observe()
            self.assertEqual(set(reads), {"surface"})
            self.assertEqual([item["id"] for item in root["items"]], ["surface"])
            self.assertEqual(root["entry"], [-2, 0, 0])
            self.assertEqual(root["focus"], root["entry"])
            self.assertIn("cell:-1:0:0", [cell["id"] for cell in root["descent_candidates"]])

            reads.clear()
            child = encounter(self.field, cursor=root["cursor"], descend="cell:-1:0:0")
            self.assertEqual(set(reads), {"conditions"})
            self.assertEqual([item["id"] for item in child["items"]], ["conditions"])
            self.assertEqual(child["entry"], root["entry"])
            self.assertEqual(child["focus"], [-1, 0, 0])
            self.assertEqual(child["focus_path"], [[-2, 0, 0], [-1, 0, 0]])

            reads.clear()
            lower = encounter(self.field, cursor=child["cursor"], descend="cell:0:0:0")
            self.assertEqual(set(reads), {"evidence"})
            self.assertEqual(lower["entry"], root["entry"])
            self.assertEqual(lower["focus_path"], [[-2, 0, 0], [-1, 0, 0], [0, 0, 0]])
            self.assertEqual(decide(self.field, lower["cursor"], "recall", "evidence")["entry"], root["entry"])

    def test_one_step_reads_adjacent_judgments_then_focus_exposes_their_details(self):
        root = self.observe()
        one_step = encounter(self.field, cursor=root["cursor"], steps=1, beam=32, limit=20)
        self.assertEqual({item["id"] for item in one_step["items"]}, {"surface", "conditions"})
        self.assertEqual(one_step["kernels"], ("coverage_down",))
        lower = encounter(self.field, cursor=one_step["cursor"], descend="cell:-1:0:0")
        self.assertEqual({item["id"] for item in lower["items"]}, {"conditions", "evidence"})
        self.assertEqual(lower["entry"], root["entry"])
        evidence = next(item for item in lower["items"] if item["id"] == "evidence")
        self.assertEqual(evidence["via"], ("coverage_down",))
        self.assertEqual(evidence["entry_path"], ("coverage_down", "coverage_down"))

    def test_descent_requires_shown_adjacent_target_and_cursor_restores_path(self):
        root = self.observe()
        for target in ("cell:0:0:0", "cell:-1:100:100", "cell:-3:0:0"):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, "descent candidate"):
                encounter(self.field, cursor=root["cursor"], descend=target)
        with self.assertRaisesRegex(ValueError, "one physical entry"):
            encounter(self.field, ["second-entry"], cursor=root["cursor"])
        with self.assertRaisesRegex(ValueError, "original physical entry"):
            encounter(self.field, cursor=root["cursor"], ascend=True)
        with self.assertRaisesRegex(ValueError, "restart"):
            encounter(self.field, cursor=root["cursor"], surface_layers=(0,))

        child = encounter(self.field, cursor=root["cursor"], descend="cell:-1:0:0")
        restored = encounter(self.field, cursor=json.loads(json.dumps(child["cursor"])))
        self.assertEqual(restored["focus_path"], child["focus_path"])
        self.assertEqual(restored["entry"], root["entry"])
        returned = encounter(self.field, cursor=restored["cursor"], ascend=True)
        self.assertEqual(returned["focus_path"], [root["entry"]])
        self.assertEqual(returned["focus"], root["entry"])

    def test_surface_can_be_read_only_while_lower_layer_is_writable(self):
        page = encounter(self.field, surface_layers=(-2,), layers=(0,), via="downward",
                         steps=0, order=0, page_size=8)
        while page["kind"] != "locality":
            candidate, = page["candidates"]
            page = encounter(self.field, [candidate["id"]], cursor=page["cursor"])
        self.assertEqual(page["entry"], [-2, 0, 0])
        self.assertEqual(page["physical_layers"], [0])
        self.assertEqual(page["cells"], [])
        for action in ("reuse", "revision"):
            with self.subTest(action=action), self.assertRaisesRegex(ValueError, "writable layers"):
                decide(self.field, page["cursor"], action, "surface", note_id=f"bad-{action}",
                       body="Not in the write scope", sources=[SOURCE])

        child = encounter(self.field, cursor=page["cursor"], descend="cell:-1:0:0")
        self.assertEqual({cell["cell"][0] for cell in child["cells"]}, {0})
        created = decide(self.field, child["cursor"], "new", "cell:0:0:0", note_id="more-evidence",
                         body="A distinct lower observation", sources=[SOURCE])
        self.assertEqual(created["cell"], [0, 0, 0])
        self.assertEqual(created["entry"], page["entry"])
        lower = encounter(self.field, cursor=child["cursor"], descend="cell:0:0:0")
        revised = decide(self.field, lower["cursor"], "revision", "evidence", note_id="evidence.v2",
                         body="Corrected original evidence", sources=[SOURCE])
        self.assertEqual(revised["cell"], [0, 0, 0])
        with CoreRuntime(self.field) as core:
            self.assertEqual(core.bridges(), ())

    def test_field_configuration_starts_scope_and_cursor_freezes_observed_choices(self):
        config_path = self.field / "access/encounter.json"
        config_path.write_text(json.dumps({"surface_layers": [-2], "layers": [-2, -1, 0],
                                          "via": "downward", "steps": 0, "order": 0, "page_size": 8,
                                          "compact": True}))
        page = encounter(self.field)
        self.assertEqual(page["surface_layers"], [-2])
        self.assertEqual(page["physical_layers"], [-2, -1, 0])
        self.assertEqual(page["page_size"], 8)
        self.assertTrue(page["compact"])
        self.assertEqual([p for c in page["candidates"] for p in c["previews"]],
                         ["支撑不足提高压力；写入仍由 Host 决定。"])
        config_path.write_text(json.dumps({"surface_layers": [0], "layers": [0]}))
        resumed = encounter(self.field, cursor=page["cursor"])
        self.assertEqual(resumed["surface_layers"], [-2])
        self.assertTrue(resumed["compact"])
        fresh = encounter(self.field)
        self.assertEqual(fresh["surface_layers"], [0])
        self.assertFalse(fresh["compact"])

    def test_compact_preserves_bodies_and_choices_and_full_sources_remain_readable(self):
        sources = [f"fixture:stored-surface-source-{index}" for index in range(12)]
        body = "A complete detailed judgment with several independent fixed sources."
        save_statement(self.field, "many-sources", body, sources, (0, 0), None, layer=-2,
                       write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
        full = self.observe()
        compact = encounter(self.field, cursor=full["cursor"], compact=True)
        self.assertEqual([(item["id"], item["text"], item["cell"]) for item in compact["items"]],
                         [(item["id"], item["text"], item["cell"]) for item in full["items"]])
        self.assertEqual([cell["id"] for cell in compact["cells"]], [cell["id"] for cell in full["cells"]])
        self.assertEqual(compact["descent_candidates"], full["descent_candidates"])
        self.assertEqual(compact["entry"], full["entry"])
        for original, projected in zip(full["cells"], compact["cells"]):
            self.assertEqual(original["write_pressure"]["pressure"], projected["write_pressure"]["pressure"])
            self.assertNotIn("cell", projected["write_pressure"])
            self.assertNotIn("support_q16", projected["write_pressure"])
        note = next(item for item in compact["items"] if item["id"] == "many-sources")
        self.assertEqual(note["sources"], sources[:1])
        self.assertEqual(note["source_count"], len(sources))
        self.assertTrue(note["sources_truncated"])
        self.assertEqual(describe(self.field, "many-sources")["sources"], sources)
        resumed = encounter(self.field, cursor=json.loads(json.dumps(compact["cursor"])))
        self.assertTrue(resumed["compact"])
        self.assertEqual(resumed["items"], compact["items"])
        expanded = encounter(self.field, cursor=resumed["cursor"], compact=False)
        self.assertEqual(expanded["items"], full["items"])
        self.assertEqual(expanded["cells"], full["cells"])
        serialized = lambda page: json.dumps({key: value for key, value in page.items() if key != "cursor"},
                                            ensure_ascii=False, indent=2).encode()
        self.assertLess(len(serialized(compact)), len(serialized(full)))

    def test_installed_cli_retains_scope_and_single_entry_across_descent(self):
        cli = install(self.root / "runtime") / "scripts/memory.py"
        cursor = self.root / "session.json"

        def meet(*args):
            result = subprocess.run([sys.executable, "-I", str(cli), "project", "--field", str(self.field),
                                     "encounter", "--cursor-file", str(cursor), *map(str, args)],
                                    text=True, capture_output=True, cwd=self.root)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

        page = meet("--surface-layers", -2, "--layers", -2, -1, 0, "--steps", 0,
                    "--via", "downward", "--order", 0, "--page-size", 8)
        while page["kind"] != "locality":
            candidate, = page["candidates"]
            page = meet(candidate["id"])
        root_entry = page["entry"]
        child = meet("--descend", "cell:-1:0:0")
        self.assertEqual(child["entry"], root_entry)
        self.assertEqual(child["focus"], [-1, 0, 0])
        returned = meet("--ascend")
        self.assertEqual(returned["focus"], root_entry)
        self.assertEqual(returned["physical_layers"], [-2, -1, 0])
        compact = meet("--compact")
        self.assertTrue(compact["compact"])
        self.assertEqual(compact["items"][0]["source_count"], 1)
        self.assertTrue(meet()["compact"])
        full = meet("--full-details")
        self.assertFalse(full["compact"])
        self.assertNotIn("source_count", full["items"][0])

    def test_last_physical_layer_remains_readable_with_no_further_descent(self):
        field = self.root / "boundary"
        save_statement(field, "last", "Last admitted layer", [SOURCE], (0, 0), None, layer=64,
                       write_policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID)
        page = encounter(field, layers=(64,), steps=0, via="lateral", order=0, page_size=8, compact=True)
        while page["kind"] != "locality":
            candidate, = page["candidates"]
            page = encounter(field, [candidate["id"]], cursor=page["cursor"])
        self.assertEqual([item["id"] for item in page["items"]], ["last"])
        self.assertEqual(page["descent_candidates"], [])
        self.assertIn("outside [-64,64]", page["descent_error"])
        pressure = page["cells"][0]["write_pressure"]
        self.assertFalse(pressure["support_complete"])
        self.assertIn("geometry_error", pressure)


if __name__ == "__main__":
    unittest.main()
