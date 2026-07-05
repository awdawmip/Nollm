from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from nollm.dream_geometry.validation.cx2.validator import validate_cortex_action_plan

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT_RUNNER = REPO_ROOT / "validation/cx2/run_cx2_conformance.py"
VALIDATION_REPORT = REPO_ROOT / "validation/cx2/CX2_EXTERNAL_CORTEX_INTEGRATION_CONFORMANCE_REPORT.md"
DOCS_REPORT = REPO_ROOT / "docs/validation/CX2_EXTERNAL_CORTEX_INTEGRATION_CONFORMANCE_REPORT.md"
SUBPROCESS_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "reference/python")}


def test_cx2_report_regeneration_matches_committed_report(tmp_path) -> None:
    output = tmp_path / "report.md"
    result = subprocess.run(
        [sys.executable, str(REPORT_RUNNER), "--output", str(output)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
        cwd=REPO_ROOT,
        env=SUBPROCESS_ENV,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    generated = output.read_text(encoding="utf-8")
    assert generated == DOCS_REPORT.read_text(encoding="utf-8")
    assert generated == VALIDATION_REPORT.read_text(encoding="utf-8")
    assert "production runtime" in generated
    assert "OpenClaw connection" in generated
    assert "Traceback" not in generated
    assert "\\" not in generated


def test_cx2_two_fresh_process_reports_are_identical(tmp_path) -> None:
    first = _run_report(tmp_path / "one.md")
    second = _run_report(tmp_path / "two.md")

    assert first == second
    assert sha256(first.encode("utf-8")).hexdigest() == sha256(second.encode("utf-8")).hexdigest()
    for forbidden in (str(tmp_path), "Traceback", "AttributeError", "KeyError", "TypeError", "ValueError"):
        assert forbidden not in first


def test_cx2_report_runner_writes_only_explicit_output_path(tmp_path) -> None:
    output = tmp_path / "nested" / "cx2.md"
    before = _tree_manifest(tmp_path)
    _run_report(output)
    after = _tree_manifest(tmp_path)

    assert tuple(path for path in after if path not in before) == ("nested", "nested/cx2.md")
    for forbidden in ("field", "assembly", "recall", "cache", "database", "global-field"):
        assert not (tmp_path / forbidden).exists()


def test_cx2_c1_06_documented_plan_examples_parse_and_validate() -> None:
    prompt_plans = _marked_plan_json_blocks(REPO_ROOT / "cortex/CORTEX_PROMPT.md")
    bridge_plans = _marked_plan_json_blocks(REPO_ROOT / "docs/integration/CX2_JSON_BRIDGE_EXAMPLES.md")

    assert set(prompt_plans) == {"stable_recall"}
    assert set(bridge_plans) == {"capture_only", "mixed_explicit"}

    assert validate_cortex_action_plan(prompt_plans["stable_recall"]).intent == "recall"
    assert validate_cortex_action_plan(bridge_plans["capture_only"]).intent == "capture_only"
    mixed = validate_cortex_action_plan(bridge_plans["mixed_explicit"])
    assert mixed.intent == "mixed_explicit"
    assert mixed.capture_ref_count == 2
    assert mixed.admission_request_count == 2

    bridge_text = (REPO_ROOT / "docs/integration/CX2_JSON_BRIDGE_EXAMPLES.md").read_text(encoding="utf-8")
    assert '"kind": "nollm_cx2_cortex_action_plan_summary"' in bridge_text
    assert '"kind": "nollm_cx2_cortex_action_plan_error"' in bridge_text
    assert "not a Core execution result" in bridge_text


def _run_report(output: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(REPORT_RUNNER), "--output", str(output)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
        cwd=REPO_ROOT,
        env=SUBPROCESS_ENV,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return output.read_text(encoding="utf-8")


def _tree_manifest(root: Path) -> tuple[str, ...]:
    return tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*")))


def _marked_plan_json_blocks(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"<!-- cx2-plan:start ([a-z_]+) -->\s*```json\s*(.*?)\s*```\s*<!-- cx2-plan:end -->", re.DOTALL)
    blocks: dict[str, dict] = {}
    for name, raw_json in pattern.findall(text):
        blocks[name] = json.loads(raw_json)
    return blocks
