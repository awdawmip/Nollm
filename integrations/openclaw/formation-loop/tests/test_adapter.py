import json
from pathlib import Path
import subprocess

import pytest

from nollm_openclaw_formation.adapter import (
    AccessFormationClient, FormationAdapterError, FormationDecisionParser,
    FormationPromptBuilder, FormationResultRenderer, OpenClawEventTranslator,
    OpenClawFormationConfig, OpenClawLLMClient, formation_schema_bytes, sha256_hex,
)


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
