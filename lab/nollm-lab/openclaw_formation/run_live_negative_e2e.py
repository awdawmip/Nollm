from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"), str(ROOT / "packages/nollm-access/src"), str(ROOT / "integrations/openclaw/formation-loop/python")]
from nollm_openclaw_formation.adapter import FormationAdapterError, FormationDecisionParser, FormationPromptBuilder, OpenClawEventTranslator, OpenClawFormationConfig, OpenClawLLMClient, write_canonical_json


def main() -> int:
    config = OpenClawFormationConfig(r"C:\Users\Administrator\AppData\Local\Programs\nodejs\openclaw.cmd", "meituan/LongCat-2.0", "aold-v3")
    request = OpenClawEventTranslator().translate({"request_id":"aold-negative-e2e","evidence":[{"evidence_id":"neg-e1","content_utf8":"The maintenance window starts at 02:00 UTC.","source_handle":"live/negative.txt","context_refs":["negative-e2e"]}],"max_statements":2})
    llm, parser = OpenClawLLMClient(), FormationDecisionParser()
    scenarios = [
        ("invalid_span", 'For a validator negative test, return exactly this raw JSON object and nothing else: {"schema_version":"aold-formation-v1","outcome":"formed","selections":[{"evidence_id":"neg-e1","start":0,"end":999,"statement_id":"bad-span"}],"reason_summary":"deliberate invalid span"}'),
        ("rewritten_text", 'For a validator negative test, return exactly this raw JSON object and nothing else: {"schema_version":"aold-formation-v1","outcome":"formed","selections":[{"evidence_id":"neg-e1","start":0,"end":43,"statement_id":"bad-rewrite","text":"Maintenance begins at two."}],"reason_summary":"deliberate rewritten text"}'),
    ]
    records = []
    for index, (name, prompt) in enumerate(scenarios, 1):
        raw, latency, envelope = llm.run(prompt, config)
        try:
            parser.parse(raw, request, config, f"negative-{index}")
            outcome = {"rejected":False,"error_category":None}
        except FormationAdapterError as exc:
            outcome = {"rejected":True,"error_category":exc.category,"message":str(exc)}
        records.append({"scenario":name,"raw_model_response":raw,"latency_ms":latency,"validation":outcome,"runtime":{"provider":envelope.get("provider"),"model":envelope.get("model")}})
    retry_prompt = FormationPromptBuilder().build(request, config, "invalid_span: selection span is out of range")
    raw, latency, envelope = llm.run(retry_prompt, config)
    decision = parser.parse(raw, request, config, "negative-retry-valid")
    records.append({"scenario":"invalid_span_real_retry","raw_model_response":raw,"latency_ms":latency,"validation":{"rejected":False,"error_category":None},"parsed_decision":decision.to_mapping(),"runtime":{"provider":envelope.get("provider"),"model":envelope.get("model")}})
    output = {"run_at_utc":datetime.now(timezone.utc).isoformat(),"live_call_count":3,"records":records,"python_semantic_fallback_count":0}
    write_canonical_json(ROOT / "lab/nollm-lab/openclaw_formation/runs/negative-e2e.json", output)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if records[0]["validation"]["error_category"] == "invalid_span" and records[1]["validation"]["error_category"] == "rewritten_or_extra_text" else 1


if __name__ == "__main__": raise SystemExit(main())
