from __future__ import annotations

import ast
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from subprocess_harness import run_subprocess, subprocess_failure_message


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SUBPROCESS_TIMEOUT = 20
ALLOWED_MEMORY_INTENTS = {
    "read_none",
    "orient_only",
    "recall_surface",
    "recall_focus",
    "write_candidate",
    "ask_user_confirmation",
}
ALLOWED_FALLBACK_MODES = {"none", "lexical_card_scan"}
SAFE_TOP_LEVEL_REQUESTS = {
    "annotations_openclaw.json",
    "audit_openclaw.json",
    "history_openclaw_card.json",
    "inspect_openclaw.json",
    "ledger_openclaw.json",
    "orient.json",
    "read_openclaw_card.json",
    "review_openclaw.json",
}
SAFE_TOP_LEVEL_ACTIONS = {
    "nollm.annotations",
    "nollm.audit",
    "nollm.history",
    "nollm.inspect",
    "nollm.ledger",
    "nollm.orient",
    "nollm.read_card",
    "nollm.review",
}
REQUIRED_SAFE_RESPONSES = {
    "audit_openclaw_response.json",
    "orient_response.json",
    "inspect_openclaw_response.json",
    "review_openclaw_response.json",
    "annotations_openclaw_response.json",
    "ledger_openclaw_response.json",
    "history_openclaw_card_response.json",
    "read_openclaw_card_response.json",
}


class StaticExampleTests(unittest.TestCase):
    def test_subprocess_runs_have_explicit_timeouts(self) -> None:
        test_files = sorted((ROOT / "reference" / "python" / "tests").glob("test_*.py"))
        missing_timeouts = []
        for path in test_files:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if is_subprocess_run_call(node) and not any(keyword.arg == "timeout" for keyword in node.keywords):
                    missing_timeouts.append(f"{path.name}:{node.lineno}")
        self.assertEqual(missing_timeouts, [], "subprocess.run calls without timeout")

    def test_example_recall_digests_use_allowed_memory_intents(self) -> None:
        paths = list((ROOT / "examples").rglob("*recall_digest*.json"))
        self.assertTrue(paths, "expected at least one static recall digest example")
        for path in paths:
            digest = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn(digest.get("memory_intent"), ALLOWED_MEMORY_INTENTS, str(path))
            self.assertNotEqual(digest.get("memory_intent"), "focus", str(path))

    def test_example_recall_digests_have_valid_fallback_shape(self) -> None:
        for path in (ROOT / "examples").rglob("*recall_digest*.json"):
            digest = json.loads(path.read_text(encoding="utf-8"))
            if "fallback_mode" in digest:
                self.assertIn(digest["fallback_mode"], ALLOWED_FALLBACK_MODES, str(path))
            if "anchors_discovered_from_cards" in digest:
                self.assertIsInstance(digest["anchors_discovered_from_cards"], list, str(path))

    def test_scale_scan_tool_response_example_is_valid_json(self) -> None:
        path = ROOT / "examples" / "tool_responses" / "recall_scale_scan_response.json"
        response = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(response["ok"])
        digest = response["result"]["digest"]
        for key in (
            "active_anchor_fields",
            "scale_path",
            "lateral_recovery",
            "sufficient_scale_reached",
        ):
            self.assertIn(key, digest)
        self.assertIsInstance(digest["lateral_recovery"], list)
        self.assertIsInstance(digest["sufficient_scale_reached"], bool)
        self.assertTrue(digest["scale_path"])
        scale_item = digest["scale_path"][0]
        self.assertIsInstance(scale_item["layer"], int)
        self.assertIsInstance(scale_item["card"], str)
        self.assertIsInstance(scale_item["anchor_fields"], list)
        self.assertIn("metadata-only", scale_item["note"])

    def test_audit_tool_response_example_is_valid_json(self) -> None:
        path = ROOT / "examples" / "tool_responses" / "audit_openclaw_response.json"
        response = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(response["ok"])
        self.assertEqual(response["action"], "nollm.audit")
        for section in (
            "validation",
            "notebook",
            "cards",
            "honeycomb",
            "anchor_fields",
            "recall_digests",
            "ledger",
            "boundaries",
        ):
            self.assertIn(section, response["result"])
        self.assertTrue(all(value is False for value in response["result"]["boundaries"].values()))

    def test_orient_tool_response_example_is_valid_json(self) -> None:
        path = ROOT / "examples" / "tool_responses" / "orient_response.json"
        response = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(response["ok"])
        self.assertEqual(response["action"], "nollm.orient")
        result = response["result"]
        self.assertEqual(result["memory_intent"], "recall_surface")
        self.assertIn("candidate_anchors", result)
        self.assertIn("matched_anchors", result)
        self.assertFalse(result["new_anchor_needed"])
        self.assertEqual(response["ledger_events"], [])

    def test_review_tool_response_example_is_valid_json(self) -> None:
        path = ROOT / "examples" / "tool_responses" / "review_openclaw_response.json"
        response = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(response["ok"])
        self.assertEqual(response["action"], "nollm.review")
        result = response["result"]
        for field in ("ok", "notebook", "review_filters", "review_count", "cards"):
            self.assertIn(field, result)
        self.assertEqual(result["review_count"], 0)
        self.assertEqual(result["cards"], [])

    def test_inspect_tool_response_example_is_valid_json(self) -> None:
        path = ROOT / "examples" / "tool_responses" / "inspect_openclaw_response.json"
        response = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(response["ok"])
        self.assertEqual(response["action"], "nollm.inspect")
        result = response["result"]
        for field in ("ok", "notebook", "review_filters", "review_count", "cards"):
            self.assertIn(field, result)
        self.assertEqual(result["review_count"], 0)
        self.assertEqual(result["cards"], [])

    def test_annotations_tool_response_example_is_valid_json(self) -> None:
        path = ROOT / "examples" / "tool_responses" / "annotations_openclaw_response.json"
        response = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(response["ok"])
        self.assertEqual(response["action"], "nollm.annotations")
        result = response["result"]
        self.assertEqual(result["annotation_count"], 0)
        self.assertEqual(result["annotations"], [])
        self.assertEqual(result["object_id"], "card_0001_nollm_project_start")

    def test_ledger_tool_response_example_is_valid_json(self) -> None:
        path = ROOT / "examples" / "tool_responses" / "ledger_openclaw_response.json"
        response = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(response["ok"])
        self.assertEqual(response["action"], "nollm.ledger")
        result = response["result"]
        self.assertEqual(result["event_count"], 1)
        self.assertEqual(result["events"][0]["object_id"], "card_0001_nollm_project_start")
        self.assertNotIn("body", json.dumps(response))

    def test_history_tool_response_example_is_valid_json(self) -> None:
        path = ROOT / "examples" / "tool_responses" / "history_openclaw_card_response.json"
        response = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(response["ok"])
        self.assertEqual(response["action"], "nollm.history")
        result = response["result"]
        self.assertEqual(result["object_id"], "card_0001_nollm_project_start")
        self.assertEqual(result["event_count"], 1)
        self.assertEqual(result["events"][0]["op"], "write_card")

    def test_read_card_tool_response_example_is_valid_json(self) -> None:
        path = ROOT / "examples" / "tool_responses" / "read_openclaw_card_response.json"
        response = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(response["ok"])
        self.assertEqual(response["action"], "nollm.read_card")
        result = response["result"]
        self.assertEqual(result["id"], "card_0001_nollm_project_start")
        self.assertIn("frontmatter", result)
        self.assertIn("body", result)
        for forbidden in ("neighbors", "related_cards", "context", "ranked_cards", "semantic_matches"):
            self.assertNotIn(forbidden, result)

    def test_top_level_tool_requests_run_from_reference_python(self) -> None:
        request_paths = sorted((ROOT / "examples" / "tool_requests").glob("*.json"))
        self.assertEqual({path.name for path in request_paths}, SAFE_TOP_LEVEL_REQUESTS)
        for request_path in request_paths:
            with self.subTest(request=request_path.name):
                response = run_tool_request_against_temp_notebook(request_path)
                self.assertTrue(response["ok"], response)
                self.assertIn(response["action"], SAFE_TOP_LEVEL_ACTIONS)
                self.assertEqual(response["ledger_events"], [])
                if request_path.name == "annotations_openclaw.json":
                    self.assertEqual(response["result"]["annotation_count"], 0)
                    self.assertEqual(response["result"]["annotations"], [])
                if request_path.name == "ledger_openclaw.json":
                    self.assertEqual(response["result"]["event_count"], 1)
                if request_path.name == "history_openclaw_card.json":
                    self.assertEqual(response["result"]["event_count"], 1)
                if request_path.name == "read_openclaw_card.json":
                    self.assertEqual(response["result"]["id"], "card_0001_nollm_project_start")
        self.assert_no_source_generated_recall_artifacts()

    def test_generated_output_recall_example_runs_only_against_temp_notebook(self) -> None:
        request_path = ROOT / "examples" / "tool_requests" / "generated_output_examples" / "recall_scale_scan.json"
        response = run_tool_request_against_temp_notebook(request_path)
        self.assertTrue(response["ok"], response)
        self.assertEqual(response["action"], "nollm.recall")
        digest = response["result"]["digest"]
        self.assertEqual(digest["memory_intent"], "recall_focus")
        for key in (
            "active_anchor_fields",
            "scale_path",
            "lateral_recovery",
            "sufficient_scale_reached",
        ):
            self.assertIn(key, digest)
        self.assertTrue(digest["scale_path"])
        self.assert_no_source_generated_recall_artifacts()

    def test_response_examples_exist_for_safe_top_level_requests(self) -> None:
        missing = sorted(
            name
            for name in REQUIRED_SAFE_RESPONSES
            if not (ROOT / "examples" / "tool_responses" / name).exists()
        )
        self.assertEqual(missing, [])

    def test_mutating_annotate_example_is_template_only(self) -> None:
        top_level_actions = []
        for request_path in sorted((ROOT / "examples" / "tool_requests").glob("*.json")):
            request = json.loads(request_path.read_text(encoding="utf-8"))
            top_level_actions.append((request_path.name, request.get("action")))

        self.assertNotIn(("annotate_openclaw.json", "nollm.annotate"), top_level_actions)
        self.assertFalse(any(action in {"nollm.annotate", "nollm.write_card", "nollm.update_status", "nollm.recall"} for _name, action in top_level_actions))
        self.assertTrue((ROOT / "examples" / "tool_requests" / "templates" / "annotate_card.json").exists())

    def test_source_openclaw_has_no_generated_recall_artifacts(self) -> None:
        self.assert_no_source_generated_recall_artifacts()

    def assert_no_source_generated_recall_artifacts(self) -> None:
        generated = generated_recall_artifacts(ROOT / "examples" / "openclaw")
        self.assertEqual(generated, [], "source OpenClaw example contains generated recall artifacts")


def run_tool_request_against_temp_notebook(request_path: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        notebook = temp_root / "openclaw"
        shutil.copytree(ROOT / "examples" / "openclaw", notebook)
        remove_generated_recall_artifacts(notebook)
        request = json.loads(request_path.read_text(encoding="utf-8"))
        request["notebook_path"] = str(notebook)
        temp_request = temp_root / request_path.name
        temp_request.write_text(json.dumps(request), encoding="utf-8")
        completed = run_subprocess(
            [sys.executable, "-m", "nollm.cli", "tool", str(temp_request)],
            cwd=REFERENCE_PYTHON,
            timeout_seconds=SUBPROCESS_TIMEOUT,
            label=request_path.as_posix(),
        )
    if completed.returncode != 0:
        raise AssertionError(subprocess_failure_message(completed, REFERENCE_PYTHON, request_path.as_posix()))
    return json.loads(completed.stdout)


def generated_recall_artifacts(notebook: Path) -> list[str]:
    recalls = notebook / "recalls"
    return sorted(
        path.name
        for pattern in ("recall_*.json", "recall_*.md")
        for path in recalls.glob(pattern)
    )


def remove_generated_recall_artifacts(notebook: Path) -> None:
    for pattern in ("recall_*.json", "recall_*.md"):
        for path in (notebook / "recalls").glob(pattern):
            path.unlink()


def is_subprocess_run_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
    )


if __name__ == "__main__":
    unittest.main()
