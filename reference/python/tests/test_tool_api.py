from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from nollm.cli import main
from nollm.filesystem import read_card, read_ledger
from nollm.validation import validate_notebook
from test_write_read import init_notebook


REQUIRED_ACTIONS = {
    "nollm.validate",
    "nollm.audit",
    "nollm.inspect",
    "nollm.review",
    "nollm.annotate",
    "nollm.annotations",
    "nollm.orient",
    "nollm.surface",
    "nollm.focus",
    "nollm.recall",
    "nollm.write_card",
    "nollm.read_card",
    "nollm.update_status",
    "nollm.ledger",
}


def run_json_cli(args: list[str]) -> tuple[int, dict]:
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(args)
    return code, json.loads(output.getvalue())


def write_request(path: Path, request: dict) -> Path:
    request_path = path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    return request_path


def tool_request(notebook: Path, action: str, payload: dict) -> dict:
    return {
        "protocol": "nollm.tool.v0.1",
        "action": action,
        "notebook_path": str(notebook),
        "input": payload,
    }


class ToolApiTests(unittest.TestCase):
    def test_tool_malformed_json_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request_path = Path(tmp) / "bad_json.json"
            request_path.write_text("{ bad", encoding="utf-8")
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertNotEqual(code, 0)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "invalid_json")

    def test_tool_non_object_json_returns_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request_path = Path(tmp) / "bad_list.json"
            request_path.write_text("[]", encoding="utf-8")
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertNotEqual(code, 0)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "invalid_request")

    def test_tools_prints_manifest_with_required_actions(self) -> None:
        code, manifest = run_json_cli(["tools"])
        self.assertEqual(code, 0)
        actions = {entry["name"] for entry in manifest["actions"]}
        self.assertTrue(REQUIRED_ACTIONS.issubset(actions))

    def test_tool_request_can_run_orient(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            request = tool_request(notebook, "nollm.orient", {"query_or_task": "project:demo"})
            request["request_id"] = "req_success"
            request_path = write_request(Path(tmp), request)
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            self.assertEqual(response["request_id"], "req_success")
            self.assertEqual(response["result"]["candidate_anchors"], ["project:demo"])

    def test_tool_request_can_run_audit_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            self.write_candidate(notebook, Path(tmp), title="Audit Tool Card")
            event_count_before = len(read_ledger(notebook))
            files_before = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            request = tool_request(notebook, "nollm.audit", {"format": "json"})
            request["request_id"] = "req_audit"
            request_path = write_request(Path(tmp), request)

            code, response = run_json_cli(["tool", str(request_path)])

            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            self.assertEqual(response["request_id"], "req_audit")
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
            self.assertEqual(len(read_ledger(notebook)), event_count_before)
            files_after = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            self.assertEqual(files_after, files_before)

    def test_tool_request_can_run_review_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            self.write_candidate(notebook, Path(tmp), title="Review Tool Card")
            event_count_before = len(read_ledger(notebook))
            files_before = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            request = tool_request(notebook, "nollm.review", {"statuses": ["candidate"], "limit": 20})
            request["request_id"] = "req_review"
            request_path = write_request(Path(tmp), request)

            code, response = run_json_cli(["tool", str(request_path)])

            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            self.assertEqual(response["request_id"], "req_review")
            self.assertEqual(response["action"], "nollm.review")
            result = response["result"]
            for field in ("ok", "notebook", "review_filters", "review_count", "cards"):
                self.assertIn(field, result)
            self.assertEqual(result["review_count"], 1)
            self.assertEqual(result["cards"][0]["title"], "Review Tool Card")
            self.assertNotIn("body", result["cards"][0])
            self.assertEqual(len(read_ledger(notebook)), event_count_before)
            files_after = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            self.assertEqual(files_after, files_before)

    def test_tool_request_can_run_inspect_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            self.write_candidate(notebook, Path(tmp), title="Inspect Tool Card")
            event_count_before = len(read_ledger(notebook))
            files_before = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            request = tool_request(notebook, "nollm.inspect", {"statuses": ["candidate"], "limit": 20})
            request["request_id"] = "req_inspect"
            request_path = write_request(Path(tmp), request)

            code, response = run_json_cli(["tool", str(request_path)])

            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            self.assertEqual(response["request_id"], "req_inspect")
            self.assertEqual(response["action"], "nollm.inspect")
            result = response["result"]
            for field in ("ok", "notebook", "review_filters", "review_count", "cards"):
                self.assertIn(field, result)
            self.assertEqual(result["review_count"], 1)
            self.assertEqual(result["cards"][0]["title"], "Inspect Tool Card")
            self.assertNotIn("body", result["cards"][0])
            self.assertEqual(len(read_ledger(notebook)), event_count_before)
            files_after = sorted(path.relative_to(notebook).as_posix() for path in notebook.rglob("*") if path.is_file())
            self.assertEqual(files_after, files_before)

    def test_tool_review_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            self.write_candidate(notebook, Path(tmp), title="Fact Candidate")
            self.write_candidate(notebook, Path(tmp), title="Decision Candidate", card_type="decision", trust="llm-proposed")
            request_path = write_request(
                Path(tmp),
                tool_request(
                    notebook,
                    "nollm.review",
                    {
                        "statuses": ["candidate"],
                        "type": "decision",
                        "anchor": "project:demo",
                        "trust": "llm-proposed",
                        "limit": 1,
                    },
                ),
            )

            code, response = run_json_cli(["tool", str(request_path)])

            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            result = response["result"]
            self.assertEqual(result["review_count"], 1)
            self.assertEqual(result["cards"][0]["title"], "Decision Candidate")
            self.assertEqual(result["review_filters"]["statuses"], ["candidate"])
            self.assertEqual(result["review_filters"]["type"], "decision")
            self.assertEqual(result["review_filters"]["anchor"], "project:demo")
            self.assertEqual(result["review_filters"]["trust"], "llm-proposed")
            self.assertEqual(result["review_filters"]["limit"], 1)

    def test_tool_review_rejects_invalid_status_type_and_trust(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            cases = [
                ({"statuses": ["needs_review"]}, "invalid_status"),
                ({"type": "unknown"}, "invalid_type"),
                ({"trust": "trusted"}, "invalid_trust"),
            ]
            for payload, expected_code in cases:
                with self.subTest(expected_code=expected_code):
                    request_path = write_request(Path(tmp), tool_request(notebook, "nollm.review", payload))
                    code, response = run_json_cli(["tool", str(request_path)])
                    self.assertNotEqual(code, 0)
                    self.assertFalse(response["ok"])
                    self.assertEqual(response["error"]["code"], expected_code)

    def test_tool_request_can_run_recall_and_create_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            self.write_candidate(notebook, Path(tmp), title="Recall Tool Card")
            request_path = write_request(Path(tmp), tool_request(notebook, "nollm.recall", {"query_or_task": "recall tool card"}))
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            self.assertTrue(Path(response["result"]["json_path"]).exists())
            self.assertTrue(Path(response["result"]["markdown_path"]).exists())

    def test_tool_recall_response_includes_scale_scan_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            payload = self.write_payload(title="Scale Scan Contract")
            payload.update(self.valid_architecture_metadata())
            request_path = write_request(Path(tmp), tool_request(notebook, "nollm.write_card", payload))
            code, write_response = run_json_cli(["tool", str(request_path)])
            self.assertEqual(code, 0)
            self.assertTrue(write_response["ok"])

            recall_path = write_request(
                Path(tmp),
                tool_request(notebook, "nollm.recall", {"query_or_task": "project:demo scale scan contract"}),
            )
            code, response = run_json_cli(["tool", str(recall_path)])

            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            self.assertIn("digest", response["result"])
            digest = response["result"]["digest"]
            self.assertEqual(digest["active_anchor_fields"], ["architecture_is_index"])
            self.assertTrue(digest["scale_path"])
            self.assertEqual(digest["scale_path"][0]["layer"], 1)
            self.assertEqual(digest["scale_path"][0]["card"], write_response["result"]["address"])
            self.assertEqual(digest["scale_path"][0]["anchor_fields"], ["architecture_is_index"])
            self.assertIn("metadata-only", digest["scale_path"][0]["note"])
            self.assertIsInstance(digest["lateral_recovery"], list)
            self.assertIsInstance(digest["sufficient_scale_reached"], bool)
            self.assertEqual(validate_notebook(notebook), [])

    def test_tool_request_can_write_candidate_and_append_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            response = self.write_candidate(notebook, Path(tmp))
            self.assertTrue(response["ok"])
            self.assertEqual(len(response["ledger_events"]), 1)
            events = read_ledger(notebook)
            self.assertEqual(events[-1]["event_id"], response["ledger_events"][0])
            self.assertEqual(events[-1]["actor_type"], "tool")

    def test_tool_write_card_respects_provided_actor_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            request = tool_request(notebook, "nollm.write_card", self.write_payload())
            request["actor"] = "codex"
            request["actor_type"] = "llm"
            request_path = write_request(Path(tmp), request)
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            event = read_ledger(notebook)[-1]
            self.assertEqual(event["actor"], "codex")
            self.assertEqual(event["actor_type"], "llm")

    def test_tool_rejects_direct_confirmed_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            payload = self.write_payload(status="confirmed")
            request_path = write_request(Path(tmp), tool_request(notebook, "nollm.write_card", payload))
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertNotEqual(code, 0)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "invalid_status")

    def test_tool_enforces_human_approval_for_confirmed_status_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_response = self.write_candidate(notebook, Path(tmp))
            request_path = write_request(
                Path(tmp),
                tool_request(
                    notebook,
                    "nollm.update_status",
                    {
                        "card_id_or_address": write_response["result"]["address"],
                        "to": "confirmed",
                        "reason": "reviewed",
                    },
                ),
            )
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertNotEqual(code, 0)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "human_approval_required")

    def test_tool_update_status_respects_actor_metadata_with_human_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            write_response = self.write_candidate(notebook, Path(tmp))
            request = tool_request(
                notebook,
                "nollm.update_status",
                {
                    "card_id_or_address": write_response["result"]["address"],
                    "to": "confirmed",
                    "reason": "reviewed",
                    "human_approval": "Approved by test human.",
                },
            )
            request["actor"] = "codex"
            request["actor_type"] = "tool"
            request_path = write_request(Path(tmp), request)
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertEqual(code, 0)
            self.assertTrue(response["ok"])
            event = read_ledger(notebook)[-1]
            self.assertEqual(event["actor"], "codex")
            self.assertEqual(event["actor_type"], "tool")
            self.assertEqual(event["human_approval"], "Approved by test human.")

    def test_tool_rejects_unknown_action_with_structured_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            request = tool_request(notebook, "nollm.unknown", {})
            request["request_id"] = "req_error"
            request_path = write_request(Path(tmp), request)
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertNotEqual(code, 0)
            self.assertFalse(response["ok"])
            self.assertEqual(response["request_id"], "req_error")
            self.assertEqual(response["error"]["code"], "unknown_action")

    def test_tool_rejects_missing_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            request_path = write_request(Path(tmp), tool_request(notebook, "nollm.orient", {}))
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertNotEqual(code, 0)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "missing_field")

    def test_tool_write_card_preserves_optional_card_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            payload = self.write_payload()
            payload["evidence_refs"] = ["external:note"]
            payload["implications"] = ["Remember this in examples."]
            payload["do_not_infer"] = ["Do not infer automation."]
            request_path = write_request(Path(tmp), tool_request(notebook, "nollm.write_card", payload))
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertEqual(code, 0)
            front, _body, _path = read_card(notebook, response["result"]["address"])
            self.assertEqual(front["evidence_refs"], ["external:note"])
            self.assertEqual(front["implications"], ["Remember this in examples."])
            self.assertEqual(front["do_not_infer"], ["Do not infer automation."])

    def test_tool_write_card_rejects_non_list_optional_card_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            payload = self.write_payload()
            payload["evidence_refs"] = "not a list"
            request_path = write_request(Path(tmp), tool_request(notebook, "nollm.write_card", payload))
            code, response = run_json_cli(["tool", str(request_path)])
            self.assertNotEqual(code, 0)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "invalid_input")

    def test_tool_write_card_rejects_invalid_architecture_layer_without_mutation(self) -> None:
        self.assert_invalid_architecture_metadata({"layer": -1}, "layer must be a non-negative integer")

    def test_tool_write_card_rejects_invalid_architecture_rotation_without_mutation(self) -> None:
        metadata = self.valid_architecture_metadata()
        metadata["hex"]["rotation"] = 45.0
        self.assert_invalid_architecture_metadata(metadata, "hex.rotation does not match layer rotation")

    def test_tool_write_card_rejects_invalid_architecture_scale_without_mutation(self) -> None:
        metadata = self.valid_architecture_metadata()
        metadata["hex"]["scale"] = 1.0
        self.assert_invalid_architecture_metadata(metadata, "hex.scale does not match layer scale")

    def test_tool_write_card_rejects_invalid_anchor_field_weight_without_mutation(self) -> None:
        metadata = self.valid_architecture_metadata()
        metadata["anchor_fields"]["architecture_is_index"]["weight"] = 1.2
        self.assert_invalid_architecture_metadata(metadata, "anchor_fields weight out of range")

    def test_tool_write_card_rejects_invalid_scale_link_key_without_mutation(self) -> None:
        metadata = self.valid_architecture_metadata()
        metadata["scale_links"] = {"children": []}
        self.assert_invalid_architecture_metadata(metadata, "scale_links has invalid key")

    def write_payload(
        self,
        *,
        title: str = "Tool Candidate",
        status: str = "candidate",
        card_type: str = "fact",
        trust: str = "unverified",
    ) -> dict:
        return {
            "type": card_type,
            "title": title,
            "claim": "Tool bridge writes candidate cards.",
            "reason": "Tool API test.",
            "anchors": ["project:demo"],
            "source": "user_statement",
            "trust": trust,
            "status": status,
        }

    def write_candidate(
        self,
        notebook: Path,
        tmp: Path,
        *,
        title: str = "Tool Candidate",
        card_type: str = "fact",
        trust: str = "unverified",
    ) -> dict:
        request_path = write_request(tmp, tool_request(notebook, "nollm.write_card", self.write_payload(title=title, card_type=card_type, trust=trust)))
        code, response = run_json_cli(["tool", str(request_path)])
        self.assertEqual(code, 0)
        return response

    def valid_architecture_metadata(self) -> dict:
        return {
            "layer": 1,
            "hex": {"q": 0, "r": 0, "rotation": 22.5, "scale": 0.8408964153},
            "anchor_fields": {"architecture_is_index": {"weight": 0.9, "role": "primary"}},
            "scale_links": {"coarser": [], "finer": [], "overlaps": [], "recovery": []},
        }

    def assert_invalid_architecture_metadata(self, metadata: dict, expected_message: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            notebook = init_notebook(tmp)
            card_count_before = len(list((notebook / "cards").rglob("*.md")))
            event_count_before = len(read_ledger(notebook))
            payload = self.write_payload()
            payload.update(metadata)
            request_path = write_request(Path(tmp), tool_request(notebook, "nollm.write_card", payload))

            code, response = run_json_cli(["tool", str(request_path)])

            self.assertNotEqual(code, 0)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "invalid_architecture_metadata")
            self.assertIn(expected_message, response["error"]["message"])
            self.assertEqual(len(list((notebook / "cards").rglob("*.md"))), card_count_before)
            self.assertEqual(len(read_ledger(notebook)), event_count_before)


if __name__ == "__main__":
    unittest.main()
