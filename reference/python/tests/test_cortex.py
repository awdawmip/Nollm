from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from nollm.cli import main
from nollm.filesystem import read_card, read_yaml_file, write_card_file, write_yaml_file
from test_write_read import init_notebook


def add_anti_agentic_anchor(notebook: Path) -> None:
    anchors = read_yaml_file(notebook / "anchors.yaml")
    anchors["anchors"].append(
        {
            "id": "anti_agentic_memory",
            "label": "Anti-agentic memory",
            "definition": "Reasons Nollm must not become automatic agent memory.",
            "scope": "Project boundary against automatic memory systems.",
            "status": "confirmed",
            "aliases": ["Cognee", "not autonomous memory"],
            "neighbors": ["project:demo"],
            "max_aliases": 8,
            "max_neighbors": 12,
            "max_active_cards": 50,
            "created": "2026-06-12",
        }
    )
    write_yaml_file(notebook / "anchors.yaml", anchors)


def cli_json(args: list[str]) -> dict:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(args)
    assert code == 0
    return json.loads(output.getvalue())


def write_custom_card(
    notebook: Path,
    *,
    title: str,
    card_type: str = "fact",
    status: str = "candidate",
    anchor: str = "anti_agentic_memory",
    body: str = "SECRET_BODY_MARKER should not appear in orient/surface/focus by default.",
) -> str:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(
            [
                "write",
                str(notebook),
                "--type",
                card_type,
                "--title",
                title,
                "--claim",
                f"{title} claim about Nollm memory boundaries.",
                "--reason",
                "P2 cortex test.",
                "--anchor",
                anchor,
                "--source",
                "user_statement",
                "--trust",
                "unverified",
                "--status",
                status,
                "--body",
                body,
            ]
        )
    assert code == 0
    return output.getvalue().strip().splitlines()[0]


class CortexTests(unittest.TestCase):
    def test_orient_matches_anchor_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            add_anti_agentic_anchor(notebook)
            result = cli_json(["orient", str(notebook), "anti_agentic_memory boundary"])
            self.assertEqual(result["matched_anchors"][0]["anchor"], "anti_agentic_memory")
            self.assertEqual(result["matched_anchors"][0]["match_type"], "id")

    def test_orient_matches_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            add_anti_agentic_anchor(notebook)
            result = cli_json(["orient", str(notebook), "why not turn Nollm into Cognee"])
            self.assertEqual(result["matched_anchors"][0]["anchor"], "anti_agentic_memory")
            self.assertEqual(result["matched_anchors"][0]["match_type"], "alias")

    def test_orient_returns_no_full_card_bodies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_custom_card(notebook, title="Project Body Secret", anchor="project:demo")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["orient", str(notebook), "project:demo"]), 0)
            self.assertNotIn("SECRET_BODY_MARKER", output.getvalue())

    def test_surface_returns_anchor_metadata_and_card_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            add_anti_agentic_anchor(notebook)
            write_custom_card(notebook, title="Surface Card")
            result = cli_json(["surface", str(notebook), "--anchor", "anti_agentic_memory"])
            self.assertEqual(result["anchor"], "anti_agentic_memory")
            self.assertEqual(result["status"], "confirmed")
            self.assertEqual(result["active_card_counts"]["fact"]["candidate"], 1)
            self.assertEqual(result["top_cards"][0]["title"], "Surface Card")

    def test_surface_does_not_output_full_body_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            add_anti_agentic_anchor(notebook)
            write_custom_card(notebook, title="Surface No Body")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["surface", str(notebook), "--anchor", "anti_agentic_memory"]), 0)
            self.assertNotIn("SECRET_BODY_MARKER", output.getvalue())

    def test_focus_prefers_confirmed_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            add_anti_agentic_anchor(notebook)
            write_custom_card(notebook, title="Candidate Boundary")
            confirmed = write_custom_card(notebook, title="Confirmed Boundary")
            self.assertEqual(
                main(
                    [
                        "status",
                        str(notebook),
                        confirmed,
                        "--to",
                        "confirmed",
                        "--reason",
                        "reviewed",
                        "--human-approval",
                        "approved by test",
                    ]
                ),
                0,
            )
            result = cli_json(["focus", str(notebook), "--anchor", "anti_agentic_memory"])
            self.assertEqual(result["cards"][0]["status"], "confirmed")
            self.assertEqual(result["cards"][0]["title"], "Confirmed Boundary")

    def test_focus_warns_on_candidate_and_hypothesis_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            add_anti_agentic_anchor(notebook)
            write_custom_card(notebook, title="Candidate Warning")
            write_custom_card(notebook, title="Hypothesis Warning", card_type="hypothesis")
            result = cli_json(["focus", str(notebook), "--anchor", "anti_agentic_memory"])
            self.assertTrue(any("Candidate card included" in warning for warning in result["warnings"]))
            self.assertTrue(any("Hypothesis card included" in warning for warning in result["warnings"]))

    def test_recall_includes_cortex_flow_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            add_anti_agentic_anchor(notebook)
            write_custom_card(notebook, title="Recall Boundary")
            self.assertEqual(main(["recall", str(notebook), "why not Cognee"]), 0)
            digest_path = sorted((notebook / "recalls").glob("*.json"))[-1]
            digest = json.loads(digest_path.read_text(encoding="utf-8"))
            self.assertIn("orientation", digest)
            self.assertIn("surfaces_read", digest)
            self.assertIn("focus_filters", digest)
            self.assertTrue((notebook / "recalls" / f"{digest_path.stem}.md").exists())

    def test_recall_includes_scale_scan_metadata_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            address = write_custom_card(notebook, title="Scale Metadata", anchor="project:demo")
            front, body, card_path = read_card(notebook, address)
            front.update(
                {
                    "layer": 1,
                    "hex": {"q": 0, "r": 0, "rotation": 22.5, "scale": 0.8408964153},
                    "anchor_fields": {
                        "architecture_is_index": {"weight": 0.9, "role": "primary"},
                        "sqlite_audit_projection": {"weight": 0.5, "role": "supporting"},
                    },
                    "scale_links": {"coarser": [], "finer": [], "overlaps": [], "recovery": []},
                }
            )
            write_card_file(card_path, front, body)

            self.assertEqual(main(["recall", str(notebook), "project:demo"]), 0)
            digest_path = sorted((notebook / "recalls").glob("*.json"))[-1]
            digest = json.loads(digest_path.read_text(encoding="utf-8"))
            markdown = (notebook / "recalls" / f"{digest_path.stem}.md").read_text(encoding="utf-8")

            self.assertEqual(digest["active_anchor_fields"], ["architecture_is_index", "sqlite_audit_projection"])
            self.assertEqual(digest["scale_path"][0]["layer"], 1)
            self.assertEqual(digest["scale_path"][0]["card"], address)
            self.assertEqual(digest["scale_path"][0]["anchor_fields"], ["architecture_is_index", "sqlite_audit_projection"])
            self.assertEqual(digest["lateral_recovery"], [])
            self.assertIsInstance(digest["sufficient_scale_reached"], bool)
            self.assertTrue(digest["sufficient_scale_reached"])
            self.assertIn("active_anchor_fields", markdown)
            self.assertIn("scale_path", markdown)

    def test_recall_emits_only_allowed_memory_intent_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_custom_card(notebook, title="Allowed Intent", anchor="project:demo")
            self.assertEqual(main(["recall", str(notebook), "project:demo"]), 0)
            digest_path = sorted((notebook / "recalls").glob("*.json"))[-1]
            digest = json.loads(digest_path.read_text(encoding="utf-8"))
            self.assertIn(
                digest["memory_intent"],
                {
                    "read_none",
                    "orient_only",
                    "recall_surface",
                    "recall_focus",
                    "write_candidate",
                    "ask_user_confirmation",
                },
            )
            self.assertNotEqual(digest["memory_intent"], "focus")

    def test_recall_emits_recall_focus_when_cards_are_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_custom_card(notebook, title="Focused Intent", anchor="project:demo")
            self.assertEqual(main(["recall", str(notebook), "project:demo"]), 0)
            digest_path = sorted((notebook / "recalls").glob("*.json"))[-1]
            digest = json.loads(digest_path.read_text(encoding="utf-8"))
            self.assertEqual(digest["memory_intent"], "recall_focus")

    def test_anchor_oriented_recall_has_no_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_custom_card(notebook, title="No Fallback", anchor="project:demo")
            self.assertEqual(main(["recall", str(notebook), "project:demo"]), 0)
            digest_path = sorted((notebook / "recalls").glob("*.json"))[-1]
            digest = json.loads(digest_path.read_text(encoding="utf-8"))
            self.assertEqual(digest["fallback_mode"], "none")
            self.assertEqual(digest["anchors_discovered_from_cards"], [])

    def test_no_anchor_lexical_fallback_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_custom_card(notebook, title="Lexical Fallback Marker", anchor="project:demo")
            self.assertEqual(main(["recall", str(notebook), "lexical fallback marker"]), 0)
            digest_path = sorted((notebook / "recalls").glob("*.json"))[-1]
            digest = json.loads(digest_path.read_text(encoding="utf-8"))
            self.assertEqual(digest["anchors_used"], [])
            self.assertEqual(digest["fallback_mode"], "lexical_card_scan")
            self.assertIn("lower-confidence", digest["fallback_warning"])
            self.assertEqual(digest["anchors_discovered_from_cards"], ["project:demo"])

    def test_orient_anchor_shapes_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            add_anti_agentic_anchor(notebook)
            result = cli_json(["orient", str(notebook), "Cognee"])
            self.assertTrue(all(isinstance(anchor, str) for anchor in result["candidate_anchors"]))
            self.assertTrue(result["matched_anchors"])
            for match in result["matched_anchors"]:
                self.assertTrue({"anchor", "confidence", "match_type", "reason"}.issubset(match))

    def test_normative_read_depth_docs_do_not_use_old_values(self) -> None:
        root = Path(__file__).resolve().parents[3]
        docs = [
            root / "cortex" / "MEMORY_INTENT.md",
            root / "cortex" / "CORTEX_PROMPT.md",
            root / "protocol" / "ACTIONS.md",
        ]
        for doc in docs:
            for line in doc.read_text(encoding="utf-8").splitlines():
                if "read_depth" in line:
                    self.assertNotIn("shallow", line)
                    self.assertNotIn("focused", line)


if __name__ == "__main__":
    unittest.main()
