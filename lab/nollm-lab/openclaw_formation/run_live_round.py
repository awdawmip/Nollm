from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"), str(ROOT / "packages/nollm-access/src"), str(ROOT / "integrations/openclaw/formation-loop/python")]

from nollm_openclaw_formation.adapter import (  # noqa: E402
    AccessFormationClient, FormationAdapterError, FormationDecisionParser,
    FormationPromptBuilder, FormationResultRenderer, OpenClawEventTranslator,
    OpenClawFormationConfig, OpenClawLLMClient, write_canonical_json,
)


CASES = [
 ("zh-single","zh",[("证据明确：项目交付日期是2026年7月20日。","zh")]),
 ("zh-multi","zh",[("服务端口为8080。备份窗口是每周日凌晨二点。","zh")]),
 ("zh-similar","zh",[("测试环境使用只读账户。生产环境使用独立的只读账户。","zh")]),
 ("zh-negative","zh",[("除紧急修复外，不得在周五部署。","zh")]),
 ("zh-defer","zh",[("它后来改成那个方案了吗？","zh")]),
 ("en-single","en",[("The retention period is exactly 30 days.","en")]),
 ("en-multi","en",[("The API listens on port 9443. The health path is /ready.","en")]),
 ("en-defer","en",[("Can you update it when they approve?","en")]),
 ("mixed","mixed",[("生产 API endpoint is https://api.example.test/v2。","mixed")]),
 ("unicode","mixed",[("发布标签是 release-β，状态图标为 ✅。","mixed")]),
 ("multi-evidence","multi",[("订单上限为500件。","zh"),("The same order requires manager approval above 400 units.","en")]),
 ("logs","multi",[("status=failed code=E42 retry=false","log"),("E42 means the signing key is expired.","en")]),
]


def request_mapping(round_number: int, index: int, spec: tuple[str,str,list[tuple[str,str]]]) -> dict[str, object]:
    name, _, records = spec
    evidence = []
    for pos, (content, language) in enumerate(records, 1):
        evidence.append({"evidence_id":f"r{round_number}-{index:02d}-e{pos}","content_utf8":content,"source_handle":f"live/{name}-{pos}.txt","context_refs":[f"language-{language}",f"round-{round_number}"]})
    return {"request_id":f"aold-r{round_number}-{index:02d}","evidence":evidence,"max_statements":4}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True, choices=(1,2,3))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--openclaw", default=os.environ.get("OPENCLAW_COMMAND", r"C:\Users\Administrator\AppData\Local\Programs\nodejs\openclaw.cmd"))
    parser.add_argument("--model", default=os.environ.get("OPENCLAW_MODEL", "meituan/LongCat-2.0"))
    args = parser.parse_args()
    config = OpenClawFormationConfig(args.openclaw, args.model, f"aold-v{args.round}", "aold-formation-v1", 120, 1)
    translator, builder, llm, parser_, access, renderer = OpenClawEventTranslator(), FormationPromptBuilder(), OpenClawLLMClient(), FormationDecisionParser(), AccessFormationClient(), FormationResultRenderer()
    records = []
    for index, spec in enumerate(CASES, 1):
        mapping = request_mapping(args.round, index, spec)
        request = translator.translate(mapping)
        retries = 0; validation = {"ok": False}; parsed = None; rendered = None; raw = None; latency = 0; envelope_meta = None
        error = None; attempts = []
        while retries <= config.max_retries:
            prompt = builder.build(request, config, error)
            call_latency = 0; raw = None
            try:
                raw, call_latency, envelope = llm.run(prompt, config)
                latency += call_latency
                envelope_meta = {"ok":envelope.get("ok"),"capability":envelope.get("capability"),"transport":envelope.get("transport"),"provider":envelope.get("provider"),"model":envelope.get("model")}
                decision = parser_.parse(raw, request, config, f"decision-{request.request_id}-try{retries}")
                statements = access.form(request, decision)
                attempts.append({"attempt":retries,"raw_model_response":raw,"latency_ms":call_latency,"accepted":True,"error_category":None})
                parsed = decision.to_mapping(); rendered = renderer.render(request, decision, statements); validation = {"ok":True,"error_category":None}; break
            except FormationAdapterError as exc:
                error = f"{exc.category}: {exc}"; validation = {"ok":False,"error_category":exc.category,"message":str(exc)}
                attempts.append({"attempt":retries,"raw_model_response":raw,"latency_ms":call_latency,"accepted":False,"error_category":exc.category,"message":str(exc)})
                if retries == config.max_retries: break
                retries += 1
        records.append({"case_id":spec[0],"language":spec[1],"run_id":request.request_id,"run_at_utc":datetime.now(timezone.utc).isoformat(),"runtime":{"openclaw_version":"2026.6.11","interface":"infer model run","model":args.model,"envelope":envelope_meta},"prompt_version":config.prompt_version,"schema_version":config.schema_version,"input":mapping,"attempts":attempts,"raw_model_response":raw,"parsed_decision":parsed,"validation":validation,"canonical_result":rendered,"latency_ms":latency,"retry_count":retries,"human_review":{"decision":"pending","note":"pending manual review"},"python_semantic_fallback":False})
        write_canonical_json(args.output_root / "runs" / f"round-{args.round}" / f"{request.request_id}.json", records[-1])
        print(f"{request.request_id}: ok={validation['ok']} retries={retries} latency_ms={latency}", flush=True)
    write_canonical_json(args.output_root / "reports" / f"round-{args.round}-index.json", {"round":args.round,"call_count":len(records)+sum(item["retry_count"] for item in records),"case_count":len(records),"records":[item["run_id"] for item in records]})
    return 0


if __name__ == "__main__": raise SystemExit(main())
