from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nollm.tool_api import dispatch_tool_request, load_tool_manifest
from test_write_read import init_notebook


ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_REQUIRED = {"protocol", "request_id", "action", "notebook_path", "actor", "actor_type", "input"}


class IntegrationPackTests(unittest.TestCase):
    def test_tool_request_templates_are_valid_and_manifested(self) -> None:
        manifest_actions = {entry["name"] for entry in load_tool_manifest()["actions"]}
        templates = list((ROOT / "examples" / "tool_requests" / "templates").glob("*.json"))
        self.assertTrue(templates)
        for path in templates:
            template = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(TEMPLATE_REQUIRED.issubset(template), str(path))
            self.assertIn(template["action"], manifest_actions, str(path))
            self.assertIsInstance(template["input"], dict, str(path))

    def test_tool_response_examples_have_envelope_shape(self) -> None:
        responses = list((ROOT / "examples" / "tool_responses").glob("*.json"))
        self.assertTrue(responses)
        for path in responses:
            response = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("ok", response, str(path))
            self.assertIn("protocol", response, str(path))
            self.assertIn("action", response, str(path))
            self.assertTrue("result" in response or "error" in response, str(path))
            self.assertFalse(contains_invalid_focus_intent(response), str(path))

    def test_minimal_tool_workflow_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)

            write = dispatch_tool_request(
                request(notebook, "nollm.write_card", {
                    "type": "fact",
                    "title": "Workflow Memory",
                    "claim": "The tool workflow stays filesystem-first.",
                    "reason": "P4 smoke test.",
                    "anchors": ["project:demo"],
                    "source": "user_statement",
                    "trust": "unverified",
                    "status": "candidate",
                })
            )
            self.assert_envelope(write, True)

            orient = dispatch_tool_request(request(notebook, "nollm.orient", {"query_or_task": "project:demo workflow"}))
            self.assert_envelope(orient, True)

            surface = dispatch_tool_request(request(notebook, "nollm.surface", {"anchor": "project:demo"}))
            self.assert_envelope(surface, True)

            focus = dispatch_tool_request(request(notebook, "nollm.focus", {"anchor": "project:demo"}))
            self.assert_envelope(focus, True)

            review = dispatch_tool_request(request(notebook, "nollm.review", {"statuses": ["candidate"]}))
            self.assert_envelope(review, True)
            self.assertEqual(review["result"]["review_count"], 1)

            recall = dispatch_tool_request(request(notebook, "nollm.recall", {"query_or_task": "project:demo workflow"}))
            self.assert_envelope(recall, True)

            validate = dispatch_tool_request(request(notebook, "nollm.validate", {}))
            self.assert_envelope(validate, True)
            self.assertTrue(validate["result"]["pass"])

    def assert_envelope(self, response: dict, ok: bool) -> None:
        self.assertEqual(response["ok"], ok)
        self.assertEqual(response["protocol"], "nollm.tool.v0.1")
        self.assertIn("action", response)
        self.assertTrue("result" in response or "error" in response)


def request(notebook: Path, action: str, payload: dict) -> dict:
    return {
        "protocol": "nollm.tool.v0.1",
        "request_id": "test",
        "action": action,
        "notebook_path": str(notebook),
        "actor": "test_agent",
        "actor_type": "tool",
        "input": payload,
    }


def contains_invalid_focus_intent(value) -> bool:
    if isinstance(value, dict):
        if value.get("memory_intent") == "focus":
            return True
        return any(contains_invalid_focus_intent(child) for child in value.values())
    if isinstance(value, list):
        return any(contains_invalid_focus_intent(child) for child in value)
    return False


if __name__ == "__main__":
    unittest.main()
