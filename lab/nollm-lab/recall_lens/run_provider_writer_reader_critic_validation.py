from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter
import uuid


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(ROOT / "packages/nollm-core/src"),
    str(ROOT / "packages/nollm-snapshot/src"),
    str(ROOT / "packages/nollm-trace/src"),
    str(ROOT / "packages/nollm-access/src"),
    str(ROOT / "integrations/openclaw/formation-loop/python"),
]

from nollm_access import AccessMemoryLoop, MemoryStatement  # noqa: E402
from nollm_openclaw_formation.memory_loop import (  # noqa: E402
    apply_fast_recall_selection,
    build_fast_recall_prompt,
)
from nollm_openclaw_formation.sculptor import (  # noqa: E402
    build_dream_sculptor_prompt,
    parse_dream_sculptor_result,
)


SCENARIOS = (
    ("tokyo-rain", "2026年7月18日东京下午三点开始下雨。", "东京下午几点开始下雨？", "大阪今天晴天。"),
    ("asakusa-cancel", "2026年7月18日原定去浅草的行程因东京降雨取消。", "浅草行程为什么取消？", "京都的展览照常开放。"),
    ("meeting", "2026年7月18日下午四点参加线上架构会议。", "线上架构会议几点开始？", "办公室咖啡机正在清洗。"),
    ("umbrella", "2026年7月18日在东京站买了一把蓝色雨伞。", "在东京站买的雨伞是什么颜色？", "名古屋列车准点到达。"),
    ("rain-stop", "2026年7月18日东京的雨在傍晚六点停止。", "东京的雨几点停止？", "札幌夜间气温下降。"),
    ("deploy", "北辰服务的发布窗口是每周二晚上九点。", "北辰服务何时发布？", "南岸仓库周五盘点。"),
    ("retention", "审计日志的保留期是三十天。", "审计日志保留多久？", "测试账户只能读取。"),
    ("backup", "数据库备份窗口是每周日凌晨两点。", "数据库何时备份？", "前台电话在下午转接。"),
    ("review", "澄海项目每周二下午三点进行风险复盘。", "澄海项目何时复盘风险？", "星河实验室周四巡检。"),
    ("handoff", "海棠值班表每天十八点十五分完成交接确认。", "海棠值班表几点交接？", "青岚展厅九点开门。"),
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _placement(statement_id: str, candidate_id: str) -> dict[str, object]:
    return {
        "schema_version": "nollm_openclaw_surface_placement_v1",
        "outcome": "apply",
        "decision": {
            "statement_id": statement_id,
            "action": "expand_surface",
            "candidate_id": candidate_id,
            "reason_text": "Lab-only finite field fixture",
        },
    }


def _host_envelope(stdout: str) -> dict[str, object] | None:
    decoder = json.JSONDecoder()
    for offset, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(stdout[offset:])
        except json.JSONDecodeError:
            continue
        if type(value) is dict and type(value.get("result")) is dict:
            return value
    return None


def _provider_call(openclaw: Path, role: str, scenario: str, prompt: str) -> dict[str, object]:
    session = f"v311r1-{role}-{scenario}-{uuid.uuid4().hex[:8]}"
    prompt_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", suffix=".txt", delete=False) as stream:
            stream.write(prompt)
            prompt_path = Path(stream.name)
        command = [
            str(openclaw), "agent", "--agent", "nollm-dream-agent",
            "--session-id", session, "--message-file", str(prompt_path),
            "--json", "--timeout", "360",
        ]
        started = perf_counter()
        completed = subprocess.run(
            command,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=420,
        )
    finally:
        if prompt_path is not None:
            prompt_path.unlink(missing_ok=True)
    elapsed_ms = round((perf_counter() - started) * 1000, 3)
    assistant = ""
    envelope = _host_envelope(completed.stdout)
    if envelope is not None:
        payloads = envelope.get("result", {}).get("payloads", [])
        assistant = "".join(item.get("text", "") for item in payloads if type(item) is dict)
    return {
        "role": role,
        "scenario_id": scenario,
        "session_id": session,
        "exit_code": completed.returncode,
        "elapsed_ms": elapsed_ms,
        "host_stdout": completed.stdout,
        "host_stderr": completed.stderr,
        "host_stdout_sha256": _sha(completed.stdout),
        "prompt_chars": len(prompt),
        "prompt_utf8_bytes": len(prompt.encode("utf-8")),
        "prompt_sha256": _sha(prompt),
        "assistant_raw": assistant,
        "assistant_raw_chars": len(assistant),
        "assistant_raw_utf8_bytes": len(assistant.encode("utf-8")),
        "assistant_raw_sha256": _sha(assistant),
        "host_envelope_parsed": envelope is not None,
    }


def _prepare(case_root: Path, index: int, scenario: tuple[str, str, str, str]) -> dict[str, object]:
    name, fact, query, unrelated = scenario
    writer_root = case_root / name / "writer"
    reader_root = case_root / name / "reader"
    writer_root.mkdir(parents=True, exist_ok=True)
    reader_root.mkdir(parents=True, exist_ok=True)
    capture = {
        "capture_id": f"capture-provider-{index:02d}",
        "user_utf8": fact,
        "assistant_utf8": "已收到。",
        "captured_epoch_ms": 1_784_352_000_000 + index,
        "timezone_offset_minutes": 480,
    }
    writer = build_dream_sculptor_prompt([capture], str(writer_root), f"provider-writer-{index:02d}")
    with AccessMemoryLoop(reader_root) as loop:
        first = loop.placement_candidates(None, f"seed-target-{index}")[0]
        loop.apply_placement(MemoryStatement(f"target-{index}", fact), _placement(f"target-{index}", first["candidate_id"]), f"apply-target-{index}")
        candidates = loop.placement_candidates(None, f"seed-unrelated-{index}")
        second = candidates[-1]
        loop.apply_placement(MemoryStatement(f"unrelated-{index}", unrelated), _placement(f"unrelated-{index}", second["candidate_id"]), f"apply-unrelated-{index}")
    reader = build_fast_recall_prompt(query, str(reader_root), f"provider-reader-{index:02d}")
    if reader.get("status") != "entry_decision":
        raise RuntimeError(f"{name} did not produce a two-entry Reader decision")
    return {
        "index": index, "name": name, "fact": fact, "query": query, "unrelated": unrelated,
        "capture": capture, "writer": writer, "reader": reader,
        "writer_root": str(writer_root), "reader_root": str(reader_root),
    }


def _reader_result(case: dict[str, object], call: dict[str, object]) -> dict[str, object]:
    try:
        return apply_fast_recall_selection(
            call["assistant_raw"], case["reader"]["entries"], case["reader_root"],
            f"provider-reader-{case['index']:02d}",
        )
    except Exception as exc:
        return {"status": "provider_output_rejected", "error": str(exc)}


def _counterfactual(case: dict[str, object]) -> dict[str, object]:
    entries = case["reader"]["entries"]
    unrelated = next(item for item in entries if any(statement["statement_id"].startswith("unrelated-") for statement in item["statements"]))
    raw = json.dumps({"schema_version": "nollm_openclaw_single_call_entry_recall_v1", "outcome": "select", "entry_id": unrelated["entry_id"]}, separators=(",", ":"))
    return apply_fast_recall_selection(raw, entries, case["reader_root"], f"counterfactual-{case['index']:02d}")


def _critic_valid(call: dict[str, object]) -> bool:
    try:
        value = json.loads(call["assistant_raw"])
    except (json.JSONDecodeError, TypeError):
        return False
    return type(value) is dict and set(value) == {
        "causal", "reader_selected_target", "unrelated_false_reach", "note",
    }


def run(openclaw: Path, output_root: Path, evidence: Path, summary: Path, concurrency: int) -> dict[str, object]:
    cases = [_prepare(output_root, index, scenario) for index, scenario in enumerate(SCENARIOS, 1)]
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        writers = list(pool.map(lambda case: _provider_call(openclaw, "writer", case["name"], case["writer"]["prompt"]), cases))
    writer_valid = []
    for case, call in zip(cases, writers, strict=True):
        try:
            parsed = parse_dream_sculptor_result(call["assistant_raw"], [case["capture"]], case["writer"]["atlas"], f"provider-writer-{case['index']:02d}")
            writer_valid.append({"valid": True, "outcome": parsed["outcome"], "error": None})
        except Exception as exc:
            writer_valid.append({"valid": False, "outcome": None, "error": str(exc)})
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        readers = list(pool.map(lambda case: _provider_call(openclaw, "reader", case["name"], case["reader"]["prompt"]), cases))
    reader_results = [_reader_result(case, call) for case, call in zip(cases, readers, strict=True)]
    counterfactuals = [_counterfactual(case) for case in cases]
    critic_prompts = [
        "You are an independent Lab-only memory critic. Compare the Provider Writer output, actual single-entry Reader result, and forced unrelated-entry counterfactual. Return exactly one JSON object with fields causal, reader_selected_target, unrelated_false_reach, and note. Do not call tools.\n"
        f"writer_raw: {writers[index]['assistant_raw']}\nreader_result: {json.dumps(reader_results[index], ensure_ascii=False, sort_keys=True)}\n"
        f"unrelated_counterfactual: {json.dumps(counterfactuals[index], ensure_ascii=False, sort_keys=True)}"
        for index in range(len(cases))
    ]
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        critics = list(pool.map(lambda item: _provider_call(openclaw, "critic", item[0]["name"], item[1]), zip(cases, critic_prompts, strict=True)))
    critic_valid = [_critic_valid(call) for call in critics]
    records = []
    for index, case in enumerate(cases):
        records.extend((
            {"record_type": "provider_role_call", **writers[index], "writer_validation": writer_valid[index], "atlas_fingerprint": case["writer"]["atlas_fingerprint"]},
            {"record_type": "provider_role_call", **readers[index], "reader_result": reader_results[index], "counterfactual_result": counterfactuals[index]},
            {"record_type": "provider_role_call", **critics[index], "critic_valid": critic_valid[index]},
        ))
    evidence.parent.mkdir(parents=True, exist_ok=True)
    prior_line_count = 0
    if evidence.exists():
        prior_line_count = sum(1 for line in evidence.read_text(encoding="utf-8").splitlines() if line)
    encoded = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for item in records).encode("utf-8")
    with evidence.open("ab") as stream:
        stream.write(encoded)
    evidence_bytes = evidence.read_bytes()
    result = {
        "schema_version": "nollm_v311r1_provider_writer_reader_critic_summary_v1",
        "provider": "meituan/LongCat-2.0",
        "scenario_count": len(cases),
        "provider_cycle_count": len(records),
        "writer_valid_count": sum(item["valid"] for item in writer_valid),
        "reader_single_entry_success_count": sum(item.get("status") == "complete_inject" for item in reader_results),
        "critic_valid_count": sum(critic_valid),
        "provider_process_success_count": sum(item["exit_code"] == 0 for item in records),
        "provider_evidence_line_count": len(records),
        "prior_host_evidence_line_count": prior_line_count,
        "combined_evidence_line_count": prior_line_count + len(records),
        "combined_evidence_utf8_bytes": len(evidence_bytes),
        "combined_evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
        "passed": (
            len(records) == 30
            and all(item["exit_code"] == 0 for item in records)
            and all(item["valid"] for item in writer_valid)
            and all(item.get("status") == "complete_inject" for item in reader_results)
            and all(critic_valid)
        ),
    }
    summary.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openclaw", type=Path, default=Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/nodejs/openclaw.cmd")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=3, choices=range(1, 6))
    args = parser.parse_args()
    result = run(args.openclaw.resolve(), args.output_root.resolve(), args.evidence.resolve(), args.summary.resolve(), args.concurrency)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
