from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "docs" / "integration" / "openclaw" / "evidence" / "aold-natural-chat-live"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def check() -> None:
    summary = json.loads((EVIDENCE / "summary.json").read_text(encoding="utf-8"))
    cases = json.loads((EVIDENCE / "live-cases.json").read_text(encoding="utf-8"))["cases"]
    for name in ("environment.json", "runtime-inspect.json", "tool-registration.json", "gateway-status.txt", "plugin-build-validate.txt", "install.txt"):
        require((EVIDENCE / name).is_file(), f"missing {name}")
    require(summary["natural_chat_case_count"] >= 15, "natural_chat_case_count")
    require(summary["natural_chat_triggered_tool_call_count"] >= 12, "triggered tool calls")
    require(summary["real_llm_calls_through_natural_chat_tool"] >= 12, "real LLM calls")
    for name in ("direct_tool_rpc_count", "chat_command_count", "raw_tool_envelope_in_chat_count", "case_specific_prompt_injection_count", "accepted_rewritten_text_count", "accepted_invalid_span_count", "python_semantic_fallback_count"):
        require(summary[name] == 0, name)
    require(summary["normal_chat_non_trigger_control_count"] >= 3, "normal chat controls")
    require(summary["disable_control_tool_calls"] == 0, "disable control")
    require(summary["uninstall_control_tool_calls"] == 0, "uninstall control")
    require(summary["reenabled_success"] and summary["reloaded_success"], "lifecycle recovery")
    tool_ids: list[str] = []
    for case in cases:
        require(case["trigger_source"] == "normal_chat" and not case["direct_injection"], "chat provenance")
        for call in case["tool_calls"]:
            tool_ids.append(call["tool_call_id"])
            result = call["tool_result"]
            if result.get("ok") is not True:
                continue
            runtime = result["runtime"]
            require(runtime["prompt_version"] == "aold-v3", "prompt version")
            require(runtime["schema_version"] == "aold-formation-v1", "schema version")
            require(not runtime["python_semantic_fallback"], "semantic fallback")
            evidence = {item["evidence_id"]: item for item in call["request"]["evidence"]}
            for formed in result["result"]["statements"]:
                statement = formed["statement"]
                span = formed["provenance"]
                source = evidence[span["evidence_id"]]
                selected = source["content_utf8"][span["start_codepoint"]:span["end_codepoint"]]
                require(statement["content_utf8"] == selected, "accepted text differs from evidence span")
                require(statement["source_handle"] == source["source_handle"], "source inheritance")
                require(statement["context_refs"] == source["context_refs"], "context inheritance")
    require(len(tool_ids) == len(set(tool_ids)), "tool_call_id uniqueness")
    require(summary["natural_chat_case_count"] == len(cases), "summary case count")
    print(f"PASS: {len(cases)} cases, {len(tool_ids)} unique tool calls")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    require(args.check, "only --check is supported; live execution is separate")
    check()


if __name__ == "__main__":
    main()
