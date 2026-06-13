from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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

    def test_top_level_tool_requests_run_from_reference_python(self) -> None:
        request_paths = sorted((ROOT / "examples" / "tool_requests").glob("*.json"))
        self.assertTrue(request_paths, "expected runnable top-level tool request examples")
        for request_path in request_paths:
            with self.subTest(request=request_path.name):
                response = run_tool_request_against_temp_notebook(request_path)
                self.assertTrue(response["ok"], response)
                if request_path.name == "recall_scale_scan.json":
                    digest = response["result"]["digest"]
                    self.assertEqual(digest["memory_intent"], "recall_focus")
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
        self.assert_no_source_generated_recall_artifacts()

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
            request_path=request_path,
        )
    if completed.returncode != 0:
        raise AssertionError(subprocess_failure_message(completed, REFERENCE_PYTHON, request_path))
    return json.loads(completed.stdout)


def run_subprocess(command: list[str], *, cwd: Path, request_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        message = [
            f"subprocess timed out after {SUBPROCESS_TIMEOUT}s",
            f"command: {' '.join(command)}",
            f"cwd: {cwd}",
        ]
        if request_path:
            message.append(f"request: {request_path}")
        message.append(f"stdout: {exc.stdout or ''}")
        message.append(f"stderr: {exc.stderr or ''}")
        raise AssertionError("\n".join(message)) from exc


def subprocess_failure_message(completed: subprocess.CompletedProcess[str], cwd: Path, request_path: Path | None = None) -> str:
    message = [
        f"command: {' '.join(str(part) for part in completed.args)}",
        f"cwd: {cwd}",
    ]
    if request_path:
        message.append(f"request: {request_path}")
    message.append(f"exit_code: {completed.returncode}")
    message.append(f"stdout: {completed.stdout}")
    message.append(f"stderr: {completed.stderr}")
    return "\n".join(message)


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
