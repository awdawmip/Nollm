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

from nollm_access import AccessMemoryLoop, DEFAULT_FIELD_SCOPE, MemoryStatement  # noqa: E402
from nollm_core import (  # noqa: E402
    CoreRuntime,
    GeometryAddress,
    RelationGroupJunctionRequest,
)
from nollm_openclaw_formation.memory_loop import (  # noqa: E402
    apply_fast_recall_selection,
    build_fast_recall_prompt,
    verify_admitted_statements,
)
from nollm_openclaw_formation.sculptor import (  # noqa: E402
    apply_dream_sculptor_result,
    build_dream_sculptor_prompt,
    parse_dream_sculptor_result,
)


SCENARIOS = (
    ("tokyo-rain", "东京今日有降雨预警。", "该降雨预警的生效时间是下午三点。", "2026年7月18日东京降雨从下午三点开始。", "东京降雨几点开始？", "大阪今日晴朗。"),
    ("asakusa", "浅草行程安排在2026年7月18日。", "东京降雨会触发行程取消。", "2026年7月18日浅草行程因东京降雨取消。", "浅草行程为什么取消？", "京都展览照常开放。"),
    ("meeting", "架构会议安排在2026年7月18日。", "该会议的开始时间是下午四点。", "2026年7月18日下午四点参加线上架构会议。", "线上架构会议几点开始？", "办公室咖啡机正在清洗。"),
    ("umbrella", "东京站需要购买雨具。", "选定雨具的颜色是蓝色。", "2026年7月18日在东京站买了一把蓝色雨伞。", "在东京站买的雨伞是什么颜色？", "名古屋列车准点到达。"),
    ("rain-stop", "东京降雨将在傍晚结束。", "本次降雨结束时间是六点。", "2026年7月18日东京的雨在傍晚六点停止。", "东京的雨几点停止？", "札幌夜间气温下降。"),
    ("deploy", "北辰服务固定在每周二发布。", "发布窗口的时间是晚上九点。", "北辰服务的发布窗口是每周二晚上九点。", "北辰服务何时发布？", "南岸仓库周五盘点。"),
    ("retention", "审计日志采用定期保留策略。", "该策略的期限是三十天。", "审计日志的保留期是三十天。", "审计日志保留多久？", "测试账户只能读取。"),
    ("backup", "数据库备份固定在每周日执行。", "备份窗口的开始时间是凌晨两点。", "数据库备份窗口是每周日凌晨两点。", "数据库何时备份？", "前台电话在下午转接。"),
    ("review", "澄海项目每周二进行风险复盘。", "风险复盘的开始时间是下午三点。", "澄海项目每周二下午三点进行风险复盘。", "澄海项目何时复盘风险？", "星河实验室周四巡检。"),
    ("handoff", "海棠值班表每天需要交接确认。", "交接确认时间是十八点十五分。", "海棠值班表每天十八点十五分完成交接确认。", "海棠值班表几点交接？", "青岚展厅九点开门。"),
)


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _state_sha(workspace: Path) -> str:
    with CoreRuntime(workspace) as core:
        return _sha_bytes(core.export_state_bytes())


def _expand(statement_id: str, candidate_id: str) -> dict[str, object]:
    return {
        "schema_version": "nollm_openclaw_surface_placement_v1",
        "outcome": "apply",
        "decision": {
            "statement_id": statement_id,
            "action": "expand_surface",
            "candidate_id": candidate_id,
            "reason_text": "Lab initial background fixture",
        },
    }


def _seed_background(workspace: Path, index: int, scenario: tuple[str, ...]) -> dict[str, object]:
    workspace.mkdir(parents=True, exist_ok=True)
    records = []
    with AccessMemoryLoop(workspace) as loop:
        for suffix, content in (("left", scenario[1]), ("right", scenario[2]), ("unrelated", scenario[5])):
            statement_id = f"background:{index:02d}:{suffix}"
            candidate = loop.placement_candidates(None, f"background:{index:02d}:{suffix}:candidates")[-1]
            result = loop.apply_placement(
                MemoryStatement(statement_id, content),
                _expand(statement_id, candidate["candidate_id"]),
                f"background:{index:02d}:{suffix}:apply",
            )
            if result["outcome"] != "applied" or not result["durable_commit"]["reopen_verified"]:
                raise RuntimeError("background fixture did not durably apply")
            records.append(result)
    return {"placements": records, "unrelated_statement_id": f"background:{index:02d}:unrelated"}


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


def _provider_call(openclaw: Path, role: str, scenario_id: str, prompt: str, attempt: int = 1) -> dict[str, object]:
    session_id = f"v311r2-{role}-{scenario_id}-{attempt}-{uuid.uuid4().hex[:8]}"
    prompt_path: Path | None = None
    started = perf_counter()
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", suffix=".txt", delete=False) as stream:
            stream.write(prompt)
            prompt_path = Path(stream.name)
        completed = subprocess.run(
            [
                str(openclaw), "agent", "--agent", "nollm-dream-agent",
                "--session-id", session_id, "--message-file", str(prompt_path),
                "--json", "--timeout", "360",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=420,
        )
    finally:
        if prompt_path is not None:
            prompt_path.unlink(missing_ok=True)
    envelope = _host_envelope(completed.stdout)
    payloads = [] if envelope is None else envelope.get("result", {}).get("payloads", [])
    assistant_raw = "".join(item.get("text", "") for item in payloads if type(item) is dict)
    return {
        "record_type": "provider_attempt",
        "role": role,
        "scenario_id": scenario_id,
        "attempt": attempt,
        "session_id": session_id,
        "exit_code": completed.returncode,
        "elapsed_ms": round((perf_counter() - started) * 1000, 3),
        "prompt_sha256": _sha_text(prompt),
        "prompt_utf8_bytes": len(prompt.encode("utf-8")),
        "assistant_raw": assistant_raw,
        "assistant_raw_sha256": _sha_text(assistant_raw),
        "host_stdout": completed.stdout,
        "host_stderr": completed.stderr,
        "host_stdout_sha256": _sha_text(completed.stdout),
        "host_stderr_sha256": _sha_text(completed.stderr),
        "host_envelope_parsed": envelope is not None,
    }


def _groups(value: object) -> tuple[tuple[GeometryAddress, ...], ...]:
    if type(value) is not list:
        raise TypeError("relation_groups must be a list")
    return tuple(tuple(GeometryAddress.from_mapping(cell) for cell in group) for group in value)


def _junction_candidates(workspace: Path, groups: tuple[tuple[GeometryAddress, ...], ...]) -> list[dict[str, object]]:
    if not groups:
        return []
    with CoreRuntime(workspace) as core:
        return [item.to_mapping() for item in core.relation_group_junction_candidates(
            RelationGroupJunctionRequest(DEFAULT_FIELD_SCOPE, groups, 4, 2, 8)
        )]


def _ablation(workspace: Path, plan: dict[str, object], unrelated_cell: dict[str, object]) -> dict[str, object]:
    groups = _groups(plan["relation_groups"])
    original = _junction_candidates(workspace, groups)
    removed = _junction_candidates(workspace, groups[:-1]) if len(groups) > 1 else []
    replacement_group = (GeometryAddress.from_mapping(unrelated_cell),)
    replaced_groups = (*groups[:-1], replacement_group)
    replaced = [] if len(set(replaced_groups)) != len(replaced_groups) else _junction_candidates(workspace, replaced_groups)
    original_cell = None if not original else original[0]["cell"]
    removed_cell = None if not removed else removed[0]["cell"]
    replaced_cell = None if not replaced else replaced[0]["cell"]
    return {
        "relation_group_count": len(groups),
        "original_candidates": original,
        "remove_one_group_candidates": removed,
        "replace_with_unrelated_candidates": replaced,
        "reason_text_not_supplied_to_core": True,
        "effect_observed": original_cell != removed_cell or original_cell != replaced_cell,
    }


def _prepare_case(output_root: Path, index: int, scenario: tuple[str, ...]) -> dict[str, object]:
    workspace = output_root / f"{index:02d}-{scenario[0]}"
    fixture = _seed_background(workspace, index, scenario)
    initial_state_sha256 = _state_sha(workspace)
    capture = {
        "capture_id": f"causal-capture-{index:02d}",
        "user_utf8": scenario[3],
        "assistant_utf8": "已收到。",
        "captured_epoch_ms": 1_784_352_000_000 + index,
        "timezone_offset_minutes": 480,
    }
    request_id = f"causal-writer-{index:02d}"
    writer = build_dream_sculptor_prompt([capture], str(workspace), request_id)
    if writer["status"] != "sculptor_decision":
        raise RuntimeError(f"{scenario[0]} Writer Atlas is not active")
    atlas = writer["atlas"]
    certificate = atlas["coverage_certificate"]
    fixture["unrelated_cell"] = fixture["placements"][-1]["handle"]["geometry_address"]
    return {
        "index": index,
        "scenario_id": scenario[0],
        "workspace": workspace,
        "query": scenario[4],
        "capture": capture,
        "request_id": request_id,
        "writer": writer,
        "fixture": fixture,
        "initial_state_sha256": initial_state_sha256,
        "atlas_certificate": {
            key: certificate[key]
            for key in (
                "occupied_field_cell_count", "covered_field_cell_count", "uncovered_field_cell_count",
                "selected_aggregation_order", "region_count", "overflow", "order_projection_counts",
            )
        },
    }


def _validate_writer(case: dict[str, object], call: dict[str, object]) -> tuple[dict[str, object] | None, str | None]:
    try:
        parsed = parse_dream_sculptor_result(
            call["assistant_raw"], [case["capture"]], case["writer"]["atlas"], case["request_id"],
        )
        if parsed["outcome"] != "plan" or len(parsed["plans"]) != 1:
            raise ValueError("causal case requires exactly one planned Statement")
        plan = parsed["plans"][0]
        if plan["action"] not in {"new_local", "expand_surface"}:
            raise ValueError("causal Writer must create a new target Statement")
        ablation = _ablation(case["workspace"], plan, case["fixture"]["unrelated_cell"])
        if not ablation["original_candidates"]:
            raise ValueError("Writer plan has no realized bounded Junction")
        return {"parsed": parsed, "ablation": ablation}, None
    except Exception as exc:
        return None, str(exc)


def _writer_prompt(case: dict[str, object], correction: str | None = None) -> str:
    suffix = "\nThis Lab causal case combines two supplied background propositions. Resolve two geometrically distinct Atlas localities when both are semantically justified; otherwise defer honestly."
    if correction is not None:
        suffix += f"\nThe prior output was rejected without writes: {correction}. Return a corrected complete raw JSON object."
    return case["writer"]["prompt"] + suffix


def _apply_writer(case: dict[str, object], call: dict[str, object], validation: dict[str, object]) -> dict[str, object]:
    result = apply_dream_sculptor_result(
        call["assistant_raw"], [case["capture"]], case["writer"]["atlas"], str(case["workspace"]), case["request_id"],
    )
    outcomes = result.get("outcomes", [])
    if len(outcomes) != 1 or outcomes[0].get("outcome") != "applied" or outcomes[0].get("action") not in {"new_local", "expand_surface"}:
        raise RuntimeError("Writer target did not durably create exactly one Statement")
    outcome = outcomes[0]
    target_id = outcome["statement_id"]
    durable = outcome["durable_commit"]
    target_handle = durable["handle"]
    junction = outcome.get("junction")
    expected = validation["ablation"]["original_candidates"][0]
    if junction is None or junction["cell"] != expected["cell"] or not junction["all_groups_realized"]:
        raise RuntimeError("applied Junction does not match realized Core preflight")
    reopened = verify_admitted_statements([target_id], str(case["workspace"]))
    final_state_sha256 = _state_sha(case["workspace"])
    if final_state_sha256 == case["initial_state_sha256"]:
        raise RuntimeError("Writer did not change the causal field")
    return {
        "apply_result": result,
        "target_statement_id": target_id,
        "target_handle": target_handle,
        "durable_reopen": reopened,
        "final_state_sha256": final_state_sha256,
        "multi_group_realized": validation["ablation"]["relation_group_count"] >= 2,
    }


def _forced_entry(entries: list[dict[str, object]], statement_id: str) -> dict[str, object]:
    matches = [entry for entry in entries if any(item["statement_id"] == statement_id for item in entry["statements"])]
    if len(matches) != 1:
        raise RuntimeError("unrelated counterfactual entry is not uniquely available")
    return matches[0]


def _apply_reader(case: dict[str, object], writer_result: dict[str, object], call: dict[str, object]) -> dict[str, object]:
    built = case["reader"]
    actual = apply_fast_recall_selection(
        call["assistant_raw"], built["entries"], str(case["workspace"]), f"causal-reader-{case['index']:02d}",
    )
    unrelated = _forced_entry(built["entries"], case["fixture"]["unrelated_statement_id"])
    raw = json.dumps(
        {"schema_version": "nollm_openclaw_single_call_entry_recall_v1", "outcome": "select", "entry_id": unrelated["entry_id"]},
        separators=(",", ":"),
    )
    counterfactual = apply_fast_recall_selection(
        raw, built["entries"], str(case["workspace"]), f"causal-counterfactual-{case['index']:02d}",
    )
    target_id = writer_result["target_statement_id"]
    target_reached = target_id in actual.get("statement_ids", [])
    target_path = next((item for item in actual.get("selected_paths", []) if item["statement_id"] == target_id), None)
    false_reach = target_id in counterfactual.get("statement_ids", [])
    return {
        "reader_result": actual,
        "counterfactual_result": counterfactual,
        "same_final_state_sha256": _state_sha(case["workspace"]) == writer_result["final_state_sha256"],
        "target_reached": target_reached,
        "target_path": target_path,
        "unrelated_false_reach": false_reach,
        "passed": actual.get("status") == "complete_inject" and target_reached and target_path is not None and not false_reach,
    }


def _defer_probe(openclaw: Path, output_root: Path, probe_index: int) -> tuple[dict[str, object], list[dict[str, object]]]:
    workspace = output_root / f"defer-probe-{probe_index:02d}"
    records = []
    with AccessMemoryLoop(workspace) as loop:
        placements = []
        for index in range(5):
            statement_id = f"defer:{probe_index}:{index}"
            candidate = loop.placement_candidates(None, f"defer:{probe_index}:{index}:candidates")[-1]
            placements.append(loop.apply_placement(
                MemoryStatement(statement_id, f"相互独立的背景事实{probe_index}-{index}。"),
                _expand(statement_id, candidate["candidate_id"]),
                f"defer:{probe_index}:{index}:apply",
            ))
    capture = {
        "capture_id": f"defer-capture-{probe_index}",
        "user_utf8": f"请记住需要同时关联第一个和第五个远端背景事实的新增结论{probe_index}。",
        "assistant_utf8": "已收到。",
        "captured_epoch_ms": 1_784_352_100_000 + probe_index,
        "timezone_offset_minutes": 480,
    }
    request_id = f"defer-writer-{probe_index}"
    built = build_dream_sculptor_prompt([capture], str(workspace), request_id)
    call = _provider_call(openclaw, "defer-writer", f"probe-{probe_index}", built["prompt"])
    records.append(call)
    try:
        parsed = parse_dream_sculptor_result(call["assistant_raw"], [capture], built["atlas"], request_id)
        honest = parsed["outcome"] == "defer" or (
            parsed["outcome"] == "plan"
            and all(plan["action"] == "defer" or not plan["relation_groups"] for plan in parsed["plans"])
        )
        error = None
    except Exception as exc:
        parsed, honest, error = None, False, str(exc)
    return {
        "record_type": "defer_probe",
        "probe_index": probe_index,
        "workspace": str(workspace),
        "atlas_certificate": built["atlas"],
        "provider_output": call["assistant_raw"],
        "parsed": parsed,
        "honest_defer": honest,
        "error": error,
        "state_sha256": _state_sha(workspace),
    }, records


def run(openclaw: Path, output_root: Path, evidence: Path, summary_path: Path, concurrency: int) -> dict[str, object]:
    cases = [_prepare_case(output_root, index, scenario) for index, scenario in enumerate(SCENARIOS, 1)]
    provider_records: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        writer_calls = list(pool.map(lambda case: _provider_call(openclaw, "writer", case["scenario_id"], _writer_prompt(case)), cases))
    writer_results: list[dict[str, object] | None] = []
    case_records = []
    for case, first_call in zip(cases, writer_calls, strict=True):
        provider_records.append(first_call)
        validation, error = _validate_writer(case, first_call)
        call = first_call
        if validation is None:
            call = _provider_call(openclaw, "writer-correction", case["scenario_id"], _writer_prompt(case, error), 2)
            provider_records.append(call)
            validation, error = _validate_writer(case, call)
        if validation is None:
            writer_results.append(None)
            case_records.append({"record_type": "causal_case", "scenario_id": case["scenario_id"], "writer_error": error, "passed": False})
            continue
        try:
            applied = _apply_writer(case, call, validation)
        except Exception as exc:
            writer_results.append(None)
            case_records.append({"record_type": "causal_case", "scenario_id": case["scenario_id"], "writer_error": str(exc), "passed": False})
            continue
        writer_results.append(applied)
        case["reader"] = build_fast_recall_prompt(case["query"], str(case["workspace"]), f"causal-reader-{case['index']:02d}")
        if case["reader"].get("status") != "entry_decision":
            raise RuntimeError("causal Reader did not expose a finite entry decision")
        case_records.append({
            "record_type": "causal_case",
            "scenario_id": case["scenario_id"],
            "workspace": str(case["workspace"]),
            "initial_state_sha256": case["initial_state_sha256"],
            "atlas_certificate": case["atlas_certificate"],
            "atlas_fingerprint": case["writer"]["atlas_fingerprint"],
            "writer_raw": call["assistant_raw"],
            "writer_validated": validation["parsed"],
            "junction_realized_preflight": validation["ablation"]["original_candidates"],
            "lens_ablation": validation["ablation"],
            **applied,
        })
    ready = [(case, result, record) for case, result, record in zip(cases, writer_results, case_records, strict=True) if result is not None]
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        reader_calls = list(pool.map(lambda item: _provider_call(openclaw, "reader", item[0]["scenario_id"], item[0]["reader"]["prompt"]), ready))
    for (case, writer_result, record), call in zip(ready, reader_calls, strict=True):
        provider_records.append(call)
        try:
            reader = _apply_reader(case, writer_result, call)
        except Exception as exc:
            reader = {"passed": False, "reader_error": str(exc)}
        record.update({"reader_raw": call["assistant_raw"], **reader, "passed": reader["passed"] and record["lens_ablation"]["effect_observed"]})
    defer_records = []
    for probe_index in range(1, 4):
        probe, attempts = _defer_probe(openclaw, output_root, probe_index)
        defer_records.append(probe)
        provider_records.extend(attempts)
    records = [*provider_records, *case_records, *defer_records]
    encoded = b"".join(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n" for item in records)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_bytes(encoded)
    summary = {
        "schema_version": "nollm_v311r2_provider_causal_writer_field_reader_summary_v1",
        "provider": "meituan/LongCat-2.0",
        "scenario_count": len(case_records),
        "writer_durable_count": sum(record.get("durable_reopen", {}).get("reopen_verified") is True for record in case_records),
        "reader_target_reach_count": sum(record.get("target_reached") is True for record in case_records),
        "unrelated_false_reach_count": sum(record.get("unrelated_false_reach") is True for record in case_records),
        "multi_group_realized_count": sum(record.get("multi_group_realized") is True for record in case_records),
        "lens_ablation_effect_count": sum(record.get("lens_ablation", {}).get("effect_observed") is True for record in case_records),
        "honest_defer_count": sum(record["honest_defer"] for record in defer_records),
        "provider_attempt_count": len(provider_records),
        "provider_process_success_count": sum(record["exit_code"] == 0 for record in provider_records),
        "evidence_line_count": len(records),
        "evidence_utf8_bytes": len(encoded),
        "evidence_sha256": _sha_bytes(encoded),
    }
    summary["passed"] = (
        summary["writer_durable_count"] == 10
        and summary["reader_target_reach_count"] == 10
        and summary["unrelated_false_reach_count"] == 0
        and summary["multi_group_realized_count"] >= 5
        and summary["lens_ablation_effect_count"] == 10
        and summary["honest_defer_count"] >= 3
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openclaw", type=Path, default=Path(os.environ.get("APPDATA", "")) / "npm/openclaw.cmd")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, choices=range(1, 6), default=3)
    args = parser.parse_args()
    result = run(args.openclaw.resolve(), args.output_root.resolve(), args.evidence.resolve(), args.summary.resolve(), args.concurrency)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
