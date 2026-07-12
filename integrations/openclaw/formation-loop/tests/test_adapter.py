import json

import pytest

from nollm_openclaw_formation.adapter import (
    AccessFormationClient, FormationAdapterError, FormationDecisionParser,
    FormationPromptBuilder, FormationResultRenderer, OpenClawEventTranslator,
    OpenClawFormationConfig,
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
