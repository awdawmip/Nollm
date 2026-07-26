from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any

from nollm_access import (
    EvidenceSpan, RawEvidenceRecord, StatementFormationDecision,
    StatementFormationRequest, StatementSelection, assemble_formed_statements,
    validate_formation_decision,
)
from .errors import FormationAdapterError


@dataclass(frozen=True)
class OpenClawFormationConfig:
    openclaw_command: str
    model: str
    prompt_version: str = "aold-v1"
    schema_version: str = "aold-formation-v1"
    timeout_seconds: int = 120
    max_retries: int = 1


class OpenClawSessionMapper:
    def map(self, session_id: str, turn_id: str) -> str:
        if not session_id or not turn_id:
            raise FormationAdapterError("invalid_event", "session_id and turn_id are required")
        return f"openclaw:{session_id}:{turn_id}"


class OpenClawEventTranslator:
    def translate(self, payload: object) -> StatementFormationRequest:
        if type(payload) is not dict or set(payload) != {"request_id", "evidence", "max_statements"}:
            raise FormationAdapterError("invalid_event", "event must contain exact Formation request fields")
        try:
            return StatementFormationRequest.from_mapping(payload)
        except (TypeError, ValueError) as exc:
            raise FormationAdapterError("invalid_event", str(exc)) from exc


class FormationPromptBuilder:
    def build(self, request: StatementFormationRequest, config: OpenClawFormationConfig, retry_error: str | None = None) -> str:
        evidence = [item.to_mapping() for item in request.evidence]
        retry = "" if retry_error is None else f"\nPrevious output was rejected: {retry_error}. Produce a new valid result."
        iteration = ""
        if config.prompt_version in {"aold-v2", "aold-v3"}:
            iteration += "\nSelect separate spans for independently meaningful durable statements; do not merge separate sentences merely because they share one Evidence record. Consider each Evidence record independently."
        if config.prompt_version == "aold-v3":
            iteration += "\nBefore returning, recount every start/end offset from zero and verify each selected slice ends exactly at its intended source text boundary."
        return f"""You are selecting durable memory statements from supplied evidence.
Return exactly one raw JSON object, without markdown or commentary.
Never summarize, rewrite, translate, join, or invent text. Select only continuous Unicode code-point spans.
Offsets use Python/Unicode code points: start is inclusive and end is exclusive.
Use only supplied evidence_id values. Use canonical selection order by evidence_id,start,end,statement_id.
If evidence is ambiguous, incomplete, only a question/instruction, or has no durable statement, defer.
Schema {config.schema_version}:
formed = {{"schema_version":"{config.schema_version}","outcome":"formed","selections":[{{"evidence_id":"...","start":0,"end":1,"statement_id":"..."}}],"reason_summary":"short visible diagnostic"}}
defer = {{"schema_version":"{config.schema_version}","outcome":"defer","selections":[],"reason_class":"insufficient_context|no_durable_statement|ambiguous","reason_summary":"short visible diagnostic"}}
Maximum selections: {request.max_statements}
request_id: {request.request_id}
evidence: {json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}{iteration}{retry}"""


def formation_schema_bytes(config: OpenClawFormationConfig) -> bytes:
    schema = {
        "defer": {
            "outcome": "defer",
            "reason_class": ["ambiguous", "insufficient_context", "no_durable_statement"],
            "required": ["schema_version", "outcome", "selections", "reason_class", "reason_summary"],
        },
        "formed": {
            "outcome": "formed",
            "required": ["schema_version", "outcome", "selections", "reason_summary"],
            "selection_required": ["evidence_id", "start", "end", "statement_id"],
        },
        "schema_version": config.schema_version,
    }
    return json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class OpenClawLLMClient:
    def run(self, prompt: str, config: OpenClawFormationConfig) -> tuple[str, int, dict[str, Any]]:
        started = time.perf_counter()
        launcher = Path(config.openclaw_command)
        if launcher.suffix.lower() == ".cmd":
            node = launcher.with_name("node.exe")
            module = launcher.parent / "node_modules" / "openclaw" / "openclaw.mjs"
            if not node.is_file() or not module.is_file():
                raise FormationAdapterError("runtime_not_found", "OpenClaw Node launcher files are missing")
            command = [str(node), str(module)]
        else:
            command = [config.openclaw_command]
        command.extend(["infer", "model", "run", "--json", "--model", config.model, "--prompt", prompt])
        try:
            completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=config.timeout_seconds, check=False)
        except subprocess.TimeoutExpired as exc:
            raise FormationAdapterError("llm_timeout", f"OpenClaw model.run exceeded {config.timeout_seconds}s") from exc
        latency = round((time.perf_counter() - started) * 1000)
        if completed.returncode != 0:
            raise FormationAdapterError("llm_call_error", completed.stderr.strip() or f"OpenClaw exited {completed.returncode}")
        try:
            envelope = json.loads(completed.stdout)
            text = envelope["outputs"][0]["text"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise FormationAdapterError("llm_envelope_error", "invalid OpenClaw model.run envelope") from exc
        if type(text) is not str or not text.strip():
            raise FormationAdapterError("empty_output", "model returned empty output")
        return text.strip(), latency, envelope


class FormationDecisionParser:
    _common = {"schema_version", "outcome", "selections", "reason_summary"}

    def parse(self, raw: str, request: StatementFormationRequest, config: OpenClawFormationConfig, decision_id: str) -> StatementFormationDecision:
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FormationAdapterError("invalid_json", str(exc)) from exc
        if type(value) is not dict or type(value.get("outcome")) is not str:
            raise FormationAdapterError("invalid_schema", "response must be an object with outcome")
        if value.get("schema_version") != config.schema_version:
            raise FormationAdapterError("schema_version_mismatch", "unexpected schema_version")
        if type(value.get("reason_summary")) is not str or not value["reason_summary"]:
            raise FormationAdapterError("invalid_schema", "reason_summary must be non-empty text")
        outcome = value["outcome"]
        if outcome == "defer":
            if set(value) != self._common | {"reason_class"} or value.get("selections") != []:
                raise FormationAdapterError("invalid_schema", "defer response has incorrect fields")
            if value.get("reason_class") not in {"insufficient_context", "no_durable_statement", "ambiguous"}:
                raise FormationAdapterError("invalid_schema", "unknown reason_class")
            return StatementFormationDecision(decision_id, request.request_id, "defer", (), f"{value['reason_class']}: {value['reason_summary']}", "llm")
        if outcome != "formed" or set(value) != self._common or type(value.get("selections")) is not list:
            raise FormationAdapterError("invalid_schema", "formed response has incorrect fields")
        selections = []
        for item in value["selections"]:
            if type(item) is not dict or set(item) != {"evidence_id", "start", "end", "statement_id"}:
                raise FormationAdapterError("rewritten_or_extra_text", "selection has non-contract fields")
            try:
                selections.append(StatementSelection(item["statement_id"], EvidenceSpan(item["evidence_id"], item["start"], item["end"])))
            except (TypeError, ValueError) as exc:
                raise FormationAdapterError("invalid_span", str(exc)) from exc
        try:
            decision = StatementFormationDecision(decision_id, request.request_id, "formed", tuple(selections), None, "llm")
            validate_formation_decision(request, decision)
        except (TypeError, ValueError) as exc:
            message = str(exc)
            category = "invalid_evidence_reference" if "unknown evidence" in message else "invalid_span"
            raise FormationAdapterError(category, message) from exc
        return decision


class AccessFormationClient:
    def form(self, request: StatementFormationRequest, decision: StatementFormationDecision) -> tuple[object, ...]:
        return assemble_formed_statements(request, decision)


class FormationResultRenderer:
    def render(self, request: StatementFormationRequest, decision: StatementFormationDecision, statements: tuple[object, ...]) -> dict[str, object]:
        evidence = {item.evidence_id: item.content_utf8 for item in request.evidence}
        return {
            "decision": decision.to_mapping(),
            "statements": [item.to_mapping() for item in statements],
            "evidence_fallback": evidence,
        }


def write_canonical_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
