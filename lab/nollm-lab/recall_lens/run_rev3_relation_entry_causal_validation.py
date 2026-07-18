from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter
import uuid


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(ROOT / "packages/nollm-core/src"),
    str(ROOT / "packages/nollm-access/src"),
    str(ROOT / "integrations/openclaw/formation-loop/python"),
]

from nollm_access import AccessMemoryLoop, MemoryStatement  # noqa: E402
from nollm_core import CoreRuntime  # noqa: E402
from nollm_openclaw_formation.cartographer import (  # noqa: E402
    FIELD_CARTOGRAPHER_SCHEMA_VERSION,
    advance_field_cartographer,
    apply_field_cartography_result,
    build_field_cartographer_prompt,
    build_proposition_writer_prompt,
    parse_proposition_writer_result,
)
from nollm_openclaw_formation.memory_loop import (  # noqa: E402
    FAST_RECALL_SCHEMA_VERSION,
    apply_fast_recall_selection,
    build_fast_recall_prompt,
    verify_admitted_statements,
)
from run_provider_causal_writer_field_reader_validation import SCENARIOS  # noqa: E402


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
            "reason_text": "bounded Lab background fixture",
        },
    }


def _seed_background(workspace: Path, index: int, scenario: tuple[str, ...]) -> dict[str, object]:
    workspace.mkdir(parents=True, exist_ok=True)
    placements = []
    with AccessMemoryLoop(workspace) as loop:
        for suffix, content in (("left", scenario[1]), ("right", scenario[2]), ("unrelated", scenario[5])):
            statement_id = f"rev3-background:{index:02d}:{suffix}"
            candidate = loop.placement_candidates(None, f"rev3-background:{index:02d}:{suffix}:candidates")[-1]
            result = loop.apply_placement(
                MemoryStatement(statement_id, content),
                _expand(statement_id, candidate["candidate_id"]),
                f"rev3-background:{index:02d}:{suffix}:apply",
            )
            if result["outcome"] != "applied" or not result["durable_commit"]["reopen_verified"]:
                raise RuntimeError("background fixture did not durably apply")
            placements.append(result)
    return {
        "placements": placements,
        "unrelated_statement_id": f"rev3-background:{index:02d}:unrelated",
        "unrelated_cell": placements[-1]["handle"]["geometry_address"],
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
        if type(value) is dict and (type(value.get("result")) is dict or type(value.get("payloads")) is list):
            return value
    return None


def _provider_turn(
    openclaw: Path,
    role: str,
    scenario_id: str,
    prompt: str,
    session_id: str | None = None,
    turn: int = 1,
) -> dict[str, object]:
    active_session = session_id or f"v311r3-{role}-{scenario_id}-{uuid.uuid4().hex[:8]}"
    prompt_path: Path | None = None
    started = perf_counter()
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", suffix=".txt", delete=False) as stream:
            stream.write(prompt)
            prompt_path = Path(stream.name)
        completed = subprocess.run(
            [
                str(openclaw), "agent", "--agent", "nollm-dream-agent",
                "--session-id", active_session, "--message-file", str(prompt_path),
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
    payloads = [] if envelope is None else (
        envelope.get("payloads", []) if type(envelope.get("payloads")) is list
        else envelope.get("result", {}).get("payloads", [])
    )
    assistant_raw = "".join(item.get("text", "") for item in payloads if type(item) is dict)
    return {
        "record_type": "provider_attempt",
        "role": role,
        "scenario_id": scenario_id,
        "turn": turn,
        "session_id": active_session,
        "exit_code": completed.returncode,
        "elapsed_ms": round((perf_counter() - started) * 1000, 3),
        "prompt_sha256": _sha_text(prompt),
        "prompt_utf8_bytes": len(prompt.encode("utf-8")),
        "assistant_raw": assistant_raw,
        "assistant_raw_sha256": _sha_text(assistant_raw),
        "host_stdout": completed.stdout,
        "host_stderr": completed.stderr,
        "host_envelope_parsed": envelope is not None,
    }


def _prepare(output_root: Path, index: int, scenario: tuple[str, ...]) -> dict[str, object]:
    workspace = output_root / f"{index:02d}-{scenario[0]}"
    fixture = _seed_background(workspace, index, scenario)
    capture = {
        "capture_id": f"rev3-capture-{index:02d}",
        "user_utf8": scenario[3],
        "assistant_utf8": "已收到。",
        "captured_epoch_ms": 1_784_352_000_000 + index,
        "timezone_offset_minutes": 480,
    }
    request_id = f"rev3-causal-{index:02d}"
    writer = build_proposition_writer_prompt([capture], request_id, 1)
    return {
        "index": index,
        "scenario_id": scenario[0],
        "workspace": workspace,
        "query": scenario[4],
        "capture": capture,
        "request_id": request_id,
        "writer": writer,
        "fixture": fixture,
        "initial_state_sha256": _state_sha(workspace),
    }


def _prepare_existing(output_root: Path, index: int, scenario: tuple[str, ...]) -> dict[str, object]:
    workspace = output_root / f"{index:02d}-{scenario[0]}"
    if not workspace.is_dir():
        raise FileNotFoundError(f"missing resumed case workspace: {workspace}")
    capture = {
        "capture_id": f"rev3-capture-{index:02d}",
        "user_utf8": scenario[3],
        "assistant_utf8": "已收到。",
        "captured_epoch_ms": 1_784_352_000_000 + index,
        "timezone_offset_minutes": 480,
    }
    request_id = f"rev3-causal-{index:02d}"
    unrelated_statement_id = f"rev3-background:{index:02d}:unrelated"
    with AccessMemoryLoop(workspace) as loop:
        unrelated_cell = loop.binding(unrelated_statement_id)["handle"]["geometry_address"]
    return {
        "index": index,
        "scenario_id": scenario[0],
        "workspace": workspace,
        "query": scenario[4],
        "capture": capture,
        "request_id": request_id,
        "writer": build_proposition_writer_prompt([capture], request_id, 1),
        "fixture": {"unrelated_statement_id": unrelated_statement_id, "unrelated_cell": unrelated_cell},
        "initial_state_sha256": _state_sha(workspace),
    }


def _writer_prompt(case: dict[str, object]) -> str:
    return case["writer"]["prompt"] + (
        "\nFor this bounded causal validation form exactly one complete proposition. "
        "Provide exactly two future Recall Lenses grounded in distinct clauses of the supplied Capture."
    )


def _run_cartographer(openclaw: Path, case: dict[str, object], writer: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]]]:
    current = build_field_cartographer_prompt(writer, str(case["workspace"]), case["request_id"])
    records = []
    session_id = f"v311r3-cartographer-{case['scenario_id']}-{uuid.uuid4().hex[:8]}"
    while current.get("status") == "cartographer_decision" and len(records) < 4:
        turn = int(current["turn"])
        prompt = current["prompt"] + (
            "\nThis causal Lab proposition combines the two related background facts visible in the Atlas. "
            "Resolve its two Lenses to geometrically distinct support entries when justified."
        )
        call = _provider_turn(openclaw, "cartographer", case["scenario_id"], prompt, session_id, turn)
        call["atlas_page"] = current["page"]
        records.append(call)
        try:
            current = advance_field_cartographer(
                call["assistant_raw"], writer, current["page"], str(case["workspace"]),
                case["request_id"], turn,
            )
        except Exception as exc:
            current = {
                **current,
                "prompt": current["prompt"] + (
                    f"\nYour previous response was rejected without writes: {exc}. "
                    "Return one corrected action using the same visible page."
                ),
            }
    if current.get("status") != "complete" or current.get("outcome") != "plan":
        raise RuntimeError("Cartographer did not complete a placement plan within four turns")
    return current, records


def _entry_key(cell: dict[str, object]) -> str:
    return json.dumps(cell, sort_keys=True, separators=(",", ":"))


def _reader_prompt(query: str, entries: list[dict[str, object]]) -> str:
    return f"""You are a private background geometry-entry selector. Choose at most one supplied relation entry_id that is likely to reach memory useful for the query, or choose none. The target Cell and target preview are intentionally absent. Do not invent entries, facts, coordinates, topics, vectors, or graphs.
Return exactly one raw JSON object with no markdown.
select: {{"schema_version":"{FAST_RECALL_SCHEMA_VERSION}","outcome":"select","entry_id":"one supplied id"}}
none: {{"schema_version":"{FAST_RECALL_SCHEMA_VERSION}","outcome":"none","entry_id":null}}
query: {json.dumps(query, ensure_ascii=False)}
relation_entries: {json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""


def _target_path(items: list[dict[str, object]], target_id: str) -> dict[str, object] | None:
    return next((item for item in items if item.get("statement_id") == target_id), None)


def _validate_case(openclaw: Path, case: dict[str, object], writer_call: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]]]:
    writer = parse_proposition_writer_result(
        writer_call["assistant_raw"], [case["capture"]], case["request_id"],
    )
    if writer["outcome"] != "plan" or len(writer["propositions"]) != 1:
        raise RuntimeError("Writer did not produce exactly one planned proposition")
    cartography, cartographer_records = _run_cartographer(openclaw, case, writer)
    plan = cartography["plans"][0]
    resolved = [item for item in plan["lens_resolutions"] if not item["unresolved"]]
    if plan["placement_mode"] != "related_growth" or not resolved:
        raise RuntimeError("Cartographer did not resolve a related-growth entry")
    applied = apply_field_cartography_result(
        cartography, writer, [case["capture"]], str(case["workspace"]), case["request_id"],
    )
    outcomes = applied.get("outcomes", [])
    if len(outcomes) != 1 or outcomes[0].get("outcome") != "applied":
        raise RuntimeError("Cartographer plan did not durably apply")
    outcome = outcomes[0]
    target_id = outcome["statement_id"]
    target_cell = outcome["durable_commit"]["handle"]["geometry_address"]
    reopened = verify_admitted_statements([target_id], str(case["workspace"]))
    post_apply_state = _state_sha(case["workspace"])
    relation_cells = []
    seen = set()
    for item in resolved:
        key = _entry_key(item["entry_cell"])
        if key not in seen:
            relation_cells.append(item["entry_cell"])
            seen.add(key)
    if not relation_cells or _entry_key(target_cell) in seen:
        raise RuntimeError("resolved relation entries must exclude the Writer target Cell")

    forced = []
    with AccessMemoryLoop(case["workspace"]) as loop:
        direct_items = loop.local_context([target_cell], case["request_id"] + ":direct-control")
        for lens_index, resolution in enumerate(resolved, 1):
            cell = resolution["entry_cell"]
            items = loop.local_context([cell], case["request_id"] + f":forced:{lens_index}")
            target = _target_path(items, target_id)
            forced.append({
                "lens_id": resolution["lens_id"],
                "entry_cell": cell,
                "target_reached": target is not None,
                "target_path": None if target is None else target.get("path"),
                "path_nonempty": bool(target and target.get("path")),
            })

    built = build_fast_recall_prompt(case["query"], str(case["workspace"]), case["request_id"] + ":reader")
    if built.get("status") != "entry_decision":
        raise RuntimeError("Reader Atlas did not expose an entry decision")
    unrelated_cell = case["fixture"]["unrelated_cell"]
    with AccessMemoryLoop(case["workspace"]) as loop:
        unrelated_context = loop.local_context([unrelated_cell], case["request_id"] + ":unrelated-entry")
    unrelated = {
        "entry_id": "counterfactual:" + _sha_text(_entry_key(unrelated_cell)),
        "region_id": "explicit-unrelated-control",
        "entry_cell": unrelated_cell,
        "occupancy_count": len(unrelated_context),
        "statements": unrelated_context[:3],
    }
    relation_keys = {_entry_key(cell) for cell in relation_cells}
    selected_entries = []
    for entry in built["entries"]:
        if _entry_key(entry["entry_cell"]) not in relation_keys and entry["entry_id"] != unrelated["entry_id"]:
            continue
        clean = {**entry, "statements": [item for item in entry["statements"] if item.get("statement_id") != target_id]}
        selected_entries.append(clean)
    with AccessMemoryLoop(case["workspace"]) as loop:
        for cell in relation_cells:
            if any(_entry_key(item["entry_cell"]) == _entry_key(cell) for item in selected_entries):
                continue
            context = loop.local_context([cell], case["request_id"] + ":relation-entry:" + _sha_text(_entry_key(cell))[:12])
            selected_entries.append({
                "entry_id": "relation:" + _sha_text(_entry_key(cell)),
                "region_id": "explicit-resolved-relation",
                "entry_cell": cell,
                "occupancy_count": len(context),
                "statements": [item for item in context[:3] if item.get("statement_id") != target_id],
            })
    if all(item["entry_id"] != unrelated["entry_id"] for item in selected_entries):
        selected_entries.append(unrelated)
    if any(_entry_key(item["entry_cell"]) == _entry_key(target_cell) for item in selected_entries):
        raise RuntimeError("target Cell leaked into Reader candidates")
    reader_prompt = _reader_prompt(case["query"], selected_entries)
    reader_call = _provider_turn(openclaw, "reader", case["scenario_id"], reader_prompt)
    reader_calls = [reader_call]
    try:
        reader_result = apply_fast_recall_selection(
            reader_call["assistant_raw"], selected_entries, str(case["workspace"]), case["request_id"] + ":reader-apply",
        )
    except Exception as exc:
        correction_prompt = reader_prompt + (
            f"\nYour previous response was rejected without writes: {exc}. "
            "Return only one corrected raw JSON object with no outer text."
        )
        reader_call = _provider_turn(
            openclaw, "reader-correction", case["scenario_id"], correction_prompt,
            reader_call["session_id"], 2,
        )
        reader_calls.append(reader_call)
        reader_result = apply_fast_recall_selection(
            reader_call["assistant_raw"], selected_entries, str(case["workspace"]), case["request_id"] + ":reader-correction",
        )
    reader_target = _target_path(reader_result.get("selected_paths", []), target_id)
    unrelated_raw = json.dumps({
        "schema_version": FAST_RECALL_SCHEMA_VERSION,
        "outcome": "select",
        "entry_id": unrelated["entry_id"],
    }, separators=(",", ":"))
    counterfactual = apply_fast_recall_selection(
        unrelated_raw, selected_entries, str(case["workspace"]), case["request_id"] + ":counterfactual",
    )
    counterfactual_target = _target_path(counterfactual.get("selected_paths", []), target_id)
    direct_target = _target_path(direct_items, target_id)
    final_state = _state_sha(case["workspace"])
    checks = {
        "direct_target_control": direct_target is not None and direct_target.get("path") == [],
        "relation_entry_reader": reader_target is not None and bool(reader_target.get("path")),
        "forced_lens_entry_reach": bool(forced) and all(item["path_nonempty"] for item in forced),
        "unrelated_counterfactual": counterfactual_target is None,
        "read_zero_write": final_state == post_apply_state,
    }
    return {
        "record_type": "relation_entry_case",
        "scenario_id": case["scenario_id"],
        "workspace": str(case["workspace"]),
        "writer_raw": writer_call["assistant_raw"],
        "writer_result": writer,
        "cartography_result": cartography,
        "cartographer_session_id": cartographer_records[0]["session_id"],
        "cartographer_turn_count": len(cartographer_records),
        "page_certificates": [record["atlas_page"]["coverage_certificate"] for record in cartographer_records],
        "apply_result": applied,
        "durable_reopen": reopened,
        "target_statement_id": target_id,
        "target_cell": target_cell,
        "target_hidden_reader_entries": selected_entries,
        "reader_raw": reader_call["assistant_raw"],
        "reader_call_count": len(reader_calls),
        "reader_result": reader_result,
        "forced_lens_entries": forced,
        "counterfactual_result": counterfactual,
        "checks": checks,
        "initial_state_sha256": case["initial_state_sha256"],
        "final_state_sha256": final_state,
        "passed": all(checks.values()),
    }, [*cartographer_records, *reader_calls]


def _validate_case_safe(
    openclaw: Path,
    case: dict[str, object],
    writer_call: dict[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    correction_calls = []
    try:
        parse_proposition_writer_result(writer_call["assistant_raw"], [case["capture"]], case["request_id"])
    except Exception as exc:
        correction_prompt = _writer_prompt(case) + (
            f"\nYour previous response was rejected without writes: {exc}. "
            "Recalculate every Python Unicode character span exactly and return one corrected raw JSON object."
        )
        writer_call = _provider_turn(openclaw, "writer-correction", case["scenario_id"], correction_prompt, turn=2)
        correction_calls.append(writer_call)
    try:
        record, calls = _validate_case(openclaw, case, writer_call)
        return record, [*correction_calls, *calls]
    except Exception as exc:
        return ({
            "record_type": "relation_entry_case",
            "scenario_id": case["scenario_id"],
            "workspace": str(case["workspace"]),
            "writer_raw": writer_call["assistant_raw"],
            "error": str(exc),
            "passed": False,
        }, correction_calls)


def run(
    openclaw: Path,
    output_root: Path,
    evidence: Path,
    summary_path: Path,
    concurrency: int,
    resume_writers: bool = False,
) -> dict[str, object]:
    if resume_writers:
        cases = [
            (_prepare_existing if (output_root / f"{index:02d}-{scenario[0]}").is_dir() else _prepare)(output_root, index, scenario)
            for index, scenario in enumerate(SCENARIOS, 1)
        ]
        frozen = [json.loads(line) for line in evidence.read_text(encoding="utf-8").splitlines() if line]
        by_scenario = {
            item["scenario_id"]: item for item in frozen
            if item.get("record_type") == "provider_attempt" and item.get("role") in {"writer", "writer-correction"}
        }
        writer_calls = []
        for case in cases:
            call = by_scenario[case["scenario_id"]]
            envelope = _host_envelope(call["host_stdout"])
            payloads = [] if envelope is None else (
                envelope.get("payloads", []) if type(envelope.get("payloads")) is list
                else envelope.get("result", {}).get("payloads", [])
            )
            call["assistant_raw"] = "".join(item.get("text", "") for item in payloads if type(item) is dict)
            call["assistant_raw_sha256"] = _sha_text(call["assistant_raw"])
            call["host_envelope_parsed"] = envelope is not None
            writer_calls.append(call)
    else:
        cases = [_prepare(output_root, index, scenario) for index, scenario in enumerate(SCENARIOS, 1)]
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            writer_calls = list(pool.map(lambda case: _provider_turn(openclaw, "writer", case["scenario_id"], _writer_prompt(case)), cases))
    provider_records = list(writer_calls)
    case_records = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        completed_cases = list(pool.map(
            lambda pair: _validate_case_safe(openclaw, pair[0], pair[1]),
            zip(cases, writer_calls, strict=True),
        ))
    for record, calls in completed_cases:
        provider_records.extend(calls)
        case_records.append(record)
    records = [*provider_records, *case_records]
    encoded = b"".join(
        json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        for item in records
    )
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_bytes(encoded)
    summary = {
        "schema_version": "nollm_v311r3_relation_entry_causal_summary_v1",
        "provider": "meituan/LongCat-2.0",
        "scenario_count": len(case_records),
        "writer_durable_count": sum(item.get("durable_reopen", {}).get("reopen_verified") is True for item in case_records),
        "relation_entry_reader_target_reach_count": sum(item.get("checks", {}).get("relation_entry_reader") is True for item in case_records),
        "forced_lens_entry_reach_count": sum(item.get("checks", {}).get("forced_lens_entry_reach") is True for item in case_records),
        "nonempty_target_path_count": sum(item.get("checks", {}).get("relation_entry_reader") is True for item in case_records),
        "unrelated_false_reach_count": sum(item.get("checks", {}).get("unrelated_counterfactual") is False for item in case_records),
        "provider_attempt_count": len(provider_records),
        "provider_process_success_count": sum(item["exit_code"] == 0 for item in provider_records),
        "writer_provider_calls": len(writer_calls),
        "cartographer_session_count": len({item["session_id"] for item in provider_records if item["role"] == "cartographer"}),
        "cartographer_turn_count": len([item for item in provider_records if item["role"] == "cartographer"]),
        "reader_correction_count": len([item for item in provider_records if item["role"] == "reader-correction"]),
        "max_prompt_utf8_bytes": max((item["prompt_utf8_bytes"] for item in provider_records), default=0),
        "evidence_line_count": len(records),
        "evidence_utf8_bytes": len(encoded),
        "evidence_sha256": _sha_bytes(encoded),
    }
    summary["passed"] = (
        summary["writer_durable_count"] == 10
        and summary["relation_entry_reader_target_reach_count"] == 10
        and summary["forced_lens_entry_reach_count"] == 10
        and summary["unrelated_false_reach_count"] == 0
        and summary["max_prompt_utf8_bytes"] <= 65536
        and all(item.get("passed") is True for item in case_records)
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openclaw", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--resume-writers", action="store_true")
    args = parser.parse_args()
    summary = run(args.openclaw, args.output_root, args.evidence, args.summary, args.concurrency, args.resume_writers)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
