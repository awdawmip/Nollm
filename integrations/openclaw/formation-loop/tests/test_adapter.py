import json
from pathlib import Path
import subprocess
import sys

import pytest

from nollm_openclaw_formation.adapter import (
    AccessFormationClient, FormationAdapterError, FormationDecisionParser,
    FormationPromptBuilder, FormationResultRenderer, OpenClawEventTranslator,
    OpenClawFormationConfig, OpenClawLLMClient, formation_schema_bytes, sha256_hex,
)
from nollm_openclaw_formation.dream_adapter import build_dream_prompt, parse_dream_result, process_dream_result, repair_dream_json
from nollm_access import ConversationMaterial, ConversationTurn, DreamFormationRequest, FileStatementStore


REQUEST = {"request_id":"r1","evidence":[{"evidence_id":"e1","content_utf8":"Keep this exact text.","source_handle":"s.txt","context_refs":["ctx"]}],"max_statements":2}
CONFIG = OpenClawFormationConfig("openclaw.cmd", "provider/model")


def test_exact_span_round_trip_and_inheritance():
    request = OpenClawEventTranslator().translate(REQUEST)
    raw = json.dumps({"schema_version":"aold-formation-v1","outcome":"formed","selections":[{"evidence_id":"e1","start":0,"end":21,"statement_id":"s1"}],"reason_summary":"one exact statement"})
    decision = FormationDecisionParser().parse(raw, request, CONFIG, "d1")
    formed = AccessFormationClient().form(request, decision)
    rendered = FormationResultRenderer().render(request, decision, formed)
    assert rendered["statements"][0]["statement"]["content_utf8"] == "Keep this exact text."
    assert rendered["statements"][0]["statement"]["source_handle"] == "s.txt"
    assert rendered["statements"][0]["statement"]["context_refs"] == ["ctx"]


@pytest.mark.parametrize(("mutation", "category"), [
    ({"evidence_id":"missing","start":0,"end":1,"statement_id":"s"}, "invalid_evidence_reference"),
    ({"evidence_id":"e1","start":0,"end":99,"statement_id":"s"}, "invalid_span"),
    ({"evidence_id":"e1","start":0,"end":1,"statement_id":"s","text":"rewritten"}, "rewritten_or_extra_text"),
])
def test_rejects_bad_model_selection(mutation, category):
    request = OpenClawEventTranslator().translate(REQUEST)
    raw = json.dumps({"schema_version":"aold-formation-v1","outcome":"formed","selections":[mutation],"reason_summary":"diagnostic"})
    with pytest.raises(FormationAdapterError) as caught:
        FormationDecisionParser().parse(raw, request, CONFIG, "d1")
    assert caught.value.category == category


def test_defer_and_prompt_contract():
    request = OpenClawEventTranslator().translate(REQUEST)
    raw = json.dumps({"schema_version":"aold-formation-v1","outcome":"defer","selections":[],"reason_class":"insufficient_context","reason_summary":"pronoun has no referent"})
    decision = FormationDecisionParser().parse(raw, request, CONFIG, "d1")
    assert decision.outcome == "defer"
    prompt = FormationPromptBuilder().build(request, CONFIG)
    assert "Never summarize, rewrite, translate, join, or invent text" in prompt
    assert "Python/Unicode code points" in prompt


def test_prompt_and_schema_digests_are_canonical():
    request = OpenClawEventTranslator().translate(REQUEST)
    config = OpenClawFormationConfig("openclaw.cmd", "provider/model", prompt_version="aold-v3")
    first = FormationPromptBuilder().build(request, config, "invalid_span")
    second = FormationPromptBuilder().build(request, config, "invalid_span")
    assert first == second
    assert "Previous output was rejected: invalid_span" in first
    assert len(sha256_hex(first.encode("utf-8"))) == 64
    assert b'aold-formation-v1' in formation_schema_bytes(config)


def test_windows_cmd_launcher(monkeypatch, tmp_path):
    command = tmp_path / "openclaw.cmd"
    node = tmp_path / "node.exe"
    module = tmp_path / "node_modules" / "openclaw" / "openclaw.mjs"
    node.touch(); module.parent.mkdir(parents=True); module.touch()
    seen = {}
    def fake_run(args, **kwargs):
        seen["args"] = args
        return subprocess.CompletedProcess(args, 0, json.dumps({"outputs":[{"text":"ok"}]}), "")
    monkeypatch.setattr(subprocess, "run", fake_run)
    raw, _, _ = OpenClawLLMClient().run("prompt", OpenClawFormationConfig(str(command), "provider/model"))
    assert raw == "ok"
    assert seen["args"][:2] == [str(node), str(module)]


@pytest.mark.parametrize("missing", ["node", "module"])
def test_windows_cmd_launcher_missing_files(tmp_path, missing):
    command = tmp_path / "openclaw.cmd"
    node = tmp_path / "node.exe"
    module = tmp_path / "node_modules" / "openclaw" / "openclaw.mjs"
    if missing != "node": node.touch()
    if missing != "module": module.parent.mkdir(parents=True); module.touch()
    with pytest.raises(FormationAdapterError, match="launcher files are missing"):
        OpenClawLLMClient().run("prompt", OpenClawFormationConfig(str(command), "provider/model"))


def test_direct_executable_and_failure_classes(monkeypatch):
    calls = []
    def fake_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, json.dumps({"outputs":[{"text":"answer"}]}), "")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert OpenClawLLMClient().run("p", OpenClawFormationConfig("openclaw.exe", "m"))[0] == "answer"
    assert calls[0][0] == "openclaw.exe"


@pytest.mark.parametrize(("completed", "category"), [
    (subprocess.CompletedProcess([], 2, "", "failure"), "llm_call_error"),
    (subprocess.CompletedProcess([], 0, "not-json", ""), "llm_envelope_error"),
    (subprocess.CompletedProcess([], 0, json.dumps({"outputs":[{"text":""}]}), ""), "empty_output"),
])
def test_llm_failure_classes(monkeypatch, completed, category):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed)
    with pytest.raises(FormationAdapterError) as caught:
        OpenClawLLMClient().run("p", OpenClawFormationConfig("openclaw.exe", "m"))
    assert caught.value.category == category


def test_llm_timeout(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired("x", 1)))
    with pytest.raises(FormationAdapterError) as caught:
        OpenClawLLMClient().run("p", OpenClawFormationConfig("openclaw.exe", "m", timeout_seconds=1))
    assert caught.value.category == "llm_timeout"


def _dream_request():
    return DreamFormationRequest("r", ConversationMaterial("m", (ConversationTurn("user", "I prefer terse reports."),)))


def test_dream_prompt_allows_rewrite_and_forbids_tools():
    prompt = build_dream_prompt(_dream_request())
    assert "rewrite, split, merge" in prompt
    assert "Do not call tools" in prompt
    assert "exact span" not in prompt


def test_dream_v2_refines_durability_without_semantic_fallback():
    prompt = build_dream_prompt(_dream_request(), "dream-v2")
    assert "one-off requests" in prompt
    assert "assistant promise" in prompt
    with pytest.raises(FormationAdapterError, match="unsupported Dream prompt version"):
        build_dream_prompt(_dream_request(), "dream-v3")


def test_dream_default_prompt_is_p1_and_outer_text_is_allowlisted():
    assert "prompt_version: dream-json-p1" in build_dream_prompt(_dream_request())
    allowed = "Here is the requested JSON: {\"schema_version\":\"nollm_access_dream_formation_v1\",\"outcome\":\"defer\",\"drafts\":[],\"defer_reason\":\"uncertain\"}"
    assert parse_dream_result(allowed, _dream_request(), "result").outcome == "defer"
    rejected = "This contradicts the object: {\"schema_version\":\"nollm_access_dream_formation_v1\",\"outcome\":\"defer\",\"drafts\":[],\"defer_reason\":\"uncertain\"}"
    with pytest.raises(FormationAdapterError, match="unsupported outer text"):
        parse_dream_result(rejected, _dream_request(), "result")


def test_dream_result_parses_rewritten_statement_and_writes_store(tmp_path):
    raw = json.dumps({
        "schema_version": "nollm_access_dream_formation_v1", "outcome": "emit",
        "drafts": [{"draft_id": "d1", "content_utf8": "The user prefers terse reports.", "scope_hint": None, "stability_hint": None, "uncertainty_hint": None}], "defer_reason": None,
    })
    result = parse_dream_result(raw, _dream_request(), "result")
    assert result.drafts[0].content_utf8 != _dream_request().material.turns[0].content_utf8
    rendered = process_dream_result(raw, _dream_request(), "result", tmp_path)
    assert rendered["statement_store_write_count"] == 1
    statement_id = rendered["statements"][0]["statement_id"]
    assert FileStatementStore(tmp_path).get(statement_id).content_utf8 == "The user prefers terse reports."


def test_dream_statement_write_is_idempotent_and_never_overwrites(tmp_path):
    raw = json.dumps({
        "schema_version": "nollm_access_dream_formation_v1", "outcome": "emit",
        "drafts": [{"draft_id": "d1", "content_utf8": "The user prefers terse reports.", "scope_hint": None, "stability_hint": None, "uncertainty_hint": None}], "defer_reason": None,
    })
    first = process_dream_result(raw, _dream_request(), "stable-result", tmp_path)
    second = process_dream_result(raw, _dream_request(), "stable-result", tmp_path)
    assert first["statements"] == second["statements"]
    assert len(list((tmp_path / "access" / "statements").glob("*/*.json"))) == 1
    changed = raw.replace("terse reports", "expanded reports")
    with pytest.raises(FileExistsError, match="different content"):
        process_dream_result(changed, _dream_request(), "stable-result", tmp_path)


def test_dream_defer_and_invalid_structure():
    raw = json.dumps({"schema_version": "nollm_access_dream_formation_v1", "outcome": "defer", "drafts": [], "defer_reason": "uncertain"})
    assert parse_dream_result(raw, _dream_request(), "result").outcome == "defer"
    with pytest.raises(FormationAdapterError):
        parse_dream_result("{}", _dream_request(), "result")


def test_dream_emit_requires_explicit_null_defer_reason():
    raw = json.dumps({
        "schema_version": "nollm_access_dream_formation_v1", "outcome": "emit",
        "drafts": [{"draft_id": "d1", "content_utf8": "A durable fact.", "scope_hint": None, "stability_hint": None, "uncertainty_hint": None}],
        "defer_reason": None,
    })
    assert parse_dream_result(raw, _dream_request(), "result").outcome == "emit"


def test_dream_result_accepts_one_fenced_json_object():
    raw = """```json
{"schema_version":"nollm_access_dream_formation_v1","outcome":"defer","drafts":[],"defer_reason":"uncertain"}
```"""
    assert parse_dream_result(raw, _dream_request(), "result").outcome == "defer"


def test_dream_json_repair_is_limited_to_allowed_syntax():
    raw = "\ufeffJSON: {\n\"schema_version\":\"nollm_access_dream_formation_v1\",\n\"outcome\":\"defer\",\n\"drafts\":[],\n\"defer_reason\":\"keep comma, literally\",\n}"
    repaired, diagnostics = repair_dream_json(raw)
    assert json.loads(repaired)["defer_reason"] == "keep comma, literally"
    assert diagnostics["repair_types"] == ["bom", "single_object_outer_text", "trailing_comma"]
    assert diagnostics["string_values_unchanged"] is True
    assert diagnostics["fields_added"] is False
    assert diagnostics["fields_removed"] is False


@pytest.mark.parametrize("raw", [
    '{"schema_version":"nollm_access_dream_formation_v1"} and {"outcome":"defer"}',
    "{'schema_version':'nollm_access_dream_formation_v1'}",
    '{"schema_version":"nollm_access_dream_formation_v1","outcome":"defer","drafts":[],"defer_reason":"unterminated}',
])
def test_dream_json_repair_rejects_semantic_or_ambiguous_changes(raw):
    with pytest.raises((FormationAdapterError, json.JSONDecodeError)):
        parse_dream_result(raw, _dream_request(), "result")


def test_bridge_normalizes_unpaired_surrogate_before_access_contract():
    envelope = {
        "action": "build_dream_prompt", "prompt_version": "dream-v1",
        "request": {
            "request_id": "r-surrogate", "schema_version": "nollm_access_dream_formation_v1",
            "material": {"material_id": "m-surrogate", "turns": [{"role": "user", "content_utf8": "bad\udc94text"}]},
            "max_statements": 8, "max_statement_chars": 4096, "max_total_chars": 8192,
        },
    }
    completed = subprocess.run(
        [sys.executable, "-m", "nollm_openclaw_formation.bridge"],
        input=json.dumps(envelope), text=True, capture_output=True, check=True,
    )
    result = json.loads(completed.stdout)
    assert result["ok"] is True
    assert "bad\ufffdtext" in result["prompt"]
