from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nollm.companion_memory_matching import analyze_facets, classify_query
from nollm.companion_memory_store import (
    CompanionMemoryError,
    remember_native_memory,
    recall_native_memory,
    native_store_summary,
)

ACTIVE_STATUS_SCHEMA = "nollm.active_memory_status.v1"
ACTIVE_PREPARE_INPUT_SCHEMA = "nollm.active_memory_prepare.v1"
ACTIVE_PREPARE_OUTPUT_SCHEMA = "nollm.provider.prepare.v2"
ACTIVE_CAPTURE_SCHEMA = "nollm.active_memory_capture.v1"
ACTIVE_TRIAL_REPORT_SCHEMA = "nollm.active_memory_trial_report.v1"
MEMORY_CONTEXT_SCHEMA = "NOLLM_MEMORY_CONTEXT_V1"
NON_MEMORY_QUERY_MARKERS = (
    "天气",
    "气温",
    "新闻",
    "股价",
    "汇率",
    "航班",
    "路线",
    "价格",
    "weather",
    "stock",
    "news",
    "exchange rate",
)

PROMOTION_PATTERNS: list[tuple[str, str]] = [
    ("explicit_remember", r"^(?:记住|请记住|remember|remember this)\s*[：:]\s*(.+)$"),
    ("identity_name", r"^(?:我叫|我的名字是|我的姓名是)\s*(?!什么|谁|哪里|吗|呢|？|\?)(.+?)[。\.]?$"),
    ("w_marker_identity", r"^我的\s+W[0-9]+(?:-[0-9]+)?\s+(?:身份|姓名)\s+marker\s+是\s*(?!什么|谁|哪里|吗|呢|？|\?)(.+?)[。\.]?$"),
    ("identity_code", r"^我的\s+身份代号\s+是\s*(.+?)[。\.]?$"),
    ("preference", r"^(?:我偏好|我喜欢|我希望回答|我希望你)\s*(.+?)[。\.]?$"),
    ("w_marker_preference", r"^我的\s+W[0-9]+(?:-[0-9]+)?\s+标签颜色\s+marker\s+是\s*(?!什么|谁|哪里|吗|呢|？|\?)(.+?)[。\.]?$"),
    ("response_style_preference", r"^我的\s+回答风格偏好\s+是\s*(.+?)[。\.]?$"),
    ("project_decision", r"^(?:项目决定|决定|发布窗口是|发版时间是)\s*(.+?)[。\.]?$"),
    ("w_marker_release", r"^我的\s+W[0-9]+(?:-[0-9]+)?\s+发布窗口\s+marker\s+是\s*(?!什么|谁|哪里|吗|呢|？|\?)(.+?)[。\.]?$"),
]

SECRET_PATTERNS = [
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"sk-\S+", re.IGNORECASE),
    re.compile(r"ghp_\S+", re.IGNORECASE),
    re.compile(r"github_pat_\S+", re.IGNORECASE),
    re.compile(r"xox[baprs]-\S+", re.IGNORECASE),
    re.compile(r"BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY", re.IGNORECASE),
    re.compile(r"api_key\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"password\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"cookie\s*=\s*\S+", re.IGNORECASE),
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(value: str) -> str:
    # Replace lone surrogate code points that can still arrive if an upstream
    # transport decodes bytes using the wrong Windows code page. This keeps
    # hashing deterministic and crash-free without changing valid UTF-8 hashes.
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _hash_id(value: str) -> str:
    return _sha256(value)[:16]


def _is_secret(text: str) -> bool:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return True
    return False


def _normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def _is_obvious_non_memory_query(query: str) -> bool:
    normalized = _normalize_text(query).lower()
    return any(marker in normalized for marker in NON_MEMORY_QUERY_MARKERS)


def _derive_out_dir(native_store_root: Path | str) -> Path:
    """The W1 native store functions expect the parent of native-companion-v1."""
    return Path(native_store_root).resolve().parent


def _resolve_trial_root(native_store_root: Path | str, trial_root: Path | str | None) -> Path:
    if trial_root is not None:
        return Path(trial_root).resolve()
    return Path(native_store_root).resolve().parent.parent / "active-trials"


def _ensure_trial_dir(trial_root: Path | str, trial_id: str) -> Path:
    trial_dir = Path(trial_root).resolve() / trial_id
    trial_dir.mkdir(parents=True, exist_ok=True)
    return trial_dir


def _write_trial_metric(trial_dir: Path, metric: dict[str, Any]) -> None:
    path = trial_dir / "trial-metrics.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(metric, ensure_ascii=False, sort_keys=True) + "\n")


def _update_trial_manifest(trial_dir: Path, manifest: dict[str, Any]) -> None:
    path = trial_dir / "trial-manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")




def _receipt_dir(trial_root: Path | str, trial_id: str) -> Path:
    path = Path(trial_root).resolve() / trial_id / "event-receipts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _claim_event_receipt(trial_root: Path | str, trial_id: str, event_id: str) -> tuple[bool, Path]:
    receipt = _receipt_dir(trial_root, trial_id) / f"{event_id}.json"
    payload = json.dumps({"schema": "nollm.active_capture_event_receipt.v1", "event_id": event_id, "state": "claimed", "created_at": _now_iso()}, sort_keys=True) + "\n"
    try:
        fd = os.open(str(receipt), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False, receipt
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(payload)
    return True, receipt


def _commit_event_receipt(receipt: Path, summary: dict[str, Any]) -> None:
    data = {
        "schema": "nollm.active_capture_event_receipt.v1",
        "event_id": receipt.stem,
        "state": "committed",
        "committed_at": _now_iso(),
        "summary": summary,
    }
    receipt.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

def _active_error(code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    return {
        "schema": "nollm.active_memory_error.v1",
        "ok": False,
        "error": {"code": code, "message": message, "retryable": retryable},
    }


def _capture_event_id(
    trial_id: str,
    agent_id: str,
    session_id: str,
    run_id: str,
    success: bool,
    current_user_message: str,
) -> str:
    canonical = json.dumps(
        {
            "schema": "nollm.active_capture_event.v2",
            "trial_id": trial_id,
            "agent_id": agent_id,
            "session_id": session_id,
            "run_id": run_id,
            "success": success,
            "current_user_message": _normalize_text(current_user_message),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return _hash_id(canonical)


def _identity_complete(identity: dict[str, str] | None) -> bool:
    if not identity:
        return False
    return all(isinstance(identity.get(key), str) and bool(identity.get(key)) for key in ("agent_id", "session_id", "run_id"))


def active_status(native_store_root: Path | str) -> dict[str, Any]:
    out_dir = _derive_out_dir(native_store_root)
    summary = native_store_summary(out_dir)
    return {
        "schema": ACTIVE_STATUS_SCHEMA,
        "ok": True,
        "store": "nollm_native_companion",
        "native_record_count": summary.get("record_count", 0),
        "active_revision_id": summary.get("active_revision_id"),
        "python_executable": Path(os.environ.get("PYTHON_EXECUTABLE", sys.executable)).resolve().as_posix(),
        "capture_mode": "deterministic_explicit_v1",
        "trial_mode": "active_empirical_v1",
    }


def active_prepare(
    native_store_root: Path | str,
    query: str,
    budget: dict[str, int],
    trial_id: str | None = None,
    identity: dict[str, str] | None = None,
    trial_root: Path | str | None = None,
) -> dict[str, Any]:
    start = time.monotonic()
    out_dir = _derive_out_dir(native_store_root)
    if not isinstance(query, str) or not _normalize_text(query):
        return _active_error("invalid_event", "active prepare requires a non-empty query.")
    max_facts = max(1, min(20, budget.get("max_facts", 4)))
    max_chars = max(200, min(65536, budget.get("max_context_characters", 1400)))

    if _is_obvious_non_memory_query(query):
        latency_ms = int((time.monotonic() - start) * 1000)
        envelope = {
            "schema": MEMORY_CONTEXT_SCHEMA,
            "freshness": "none",
            "facts": [],
            "boundaries": [],
            "warnings": [],
            "explicit_absences": ["No Nollm native companion memory matched this query."],
        }
        if trial_id:
            trial_dir = _ensure_trial_dir(_resolve_trial_root(native_store_root, trial_root), trial_id)
            _write_trial_metric(trial_dir, {
                "event": "prepare",
                "timestamp": _now_iso(),
                "trial_id": trial_id,
                "agent_id_hash": _hash_id(identity.get("agent_id", "")) if identity else None,
                "session_id_hash": _hash_id(identity.get("session_id", "")) if identity else None,
                "run_id_hash": _hash_id(identity.get("run_id", "")) if identity else None,
                "query_hash": _hash_id(query),
                "query_class": "non_memory",
                "result_count": 0,
                "facts_returned": 0,
                "rendered_chars": len(_format_memory_context(envelope)),
                "recall_mode": "none",
                "latency_ms": latency_ms,
            })
        return {
            "schema": ACTIVE_PREPARE_OUTPUT_SCHEMA,
            "ok": True,
            "context": envelope,
            "metrics": {
                "native_record_count": native_store_summary(out_dir).get("record_count", 0),
                "result_count": 0,
                "rendered_context_characters": len(_format_memory_context(envelope)),
                "recall_mode": "none",
            },
        }

    result = recall_native_memory(out_dir, out_dir, out_dir, query=query, limit=max_facts)
    latency_ms = int((time.monotonic() - start) * 1000)

    if result.get("ok") is not True:
        error = result.get("error") if isinstance(result.get("error"), dict) else {}
        code = str(error.get("code") or "native_recall_failed")
        if trial_id:
            trial_dir = _ensure_trial_dir(_resolve_trial_root(native_store_root, trial_root), trial_id)
            _write_trial_metric(trial_dir, {
                "event": "prepare_error",
                "timestamp": _now_iso(),
                "trial_id": trial_id,
                "agent_id_hash": _hash_id(identity.get("agent_id", "")) if identity else None,
                "session_id_hash": _hash_id(identity.get("session_id", "")) if identity else None,
                "run_id_hash": _hash_id(identity.get("run_id", "")) if identity else None,
                "query_hash": _hash_id(query),
                "prepare_error_code": code,
                "latency_ms": latency_ms,
            })
        return _active_error(code, "Native active recall failed.", retryable=True)

    facts: list[dict[str, Any]] = []
    recall_mode = "none"
    if result.get("ok") and result.get("results"):
        recall_mode = result["results"][0].get("match", {}).get("mode", "lexical")
        for r in result["results"][:max_facts]:
            facts.append({
                "memory_id": r["memory_id"],
                "claim": r["text"],
                "kind": r["kind"],
                "source": "nollm_native_companion",
                "revision_id": r.get("revision_id"),
            })

    freshness = "none" if not facts else "fresh"
    envelope = {
        "schema": MEMORY_CONTEXT_SCHEMA,
        "freshness": freshness,
        "facts": facts,
        "boundaries": [],
        "warnings": [],
        "explicit_absences": [],
    }
    if not facts:
        envelope["explicit_absences"].append("No Nollm native companion memory matched this query.")

    rendered = _format_memory_context(envelope)
    if len(rendered) > max_chars:
        # Trim by dropping facts until under budget
        while len(rendered) > max_chars and facts:
            facts.pop()
            envelope["facts"] = facts
            envelope["warnings"].append("Additional matching facts omitted due to context budget.")
            rendered = _format_memory_context(envelope)
        if not facts:
            envelope["explicit_absences"].append("Matching facts exceeded context budget.")

    metrics = {
        "native_record_count": result.get("native_record_count", 0),
        "result_count": len(result.get("results", [])),
        "rendered_context_characters": len(rendered),
        "recall_mode": recall_mode,
    }

    if trial_id:
        trial_dir = _ensure_trial_dir(_resolve_trial_root(native_store_root, trial_root), trial_id)
        _write_trial_metric(trial_dir, {
            "event": "prepare",
            "timestamp": _now_iso(),
            "trial_id": trial_id,
            "agent_id_hash": _hash_id(identity.get("agent_id", "")) if identity else None,
            "session_id_hash": _hash_id(identity.get("session_id", "")) if identity else None,
            "run_id_hash": _hash_id(identity.get("run_id", "")) if identity else None,
            "query_hash": _hash_id(query),
            "query_class": classify_query(query, analyze_facets(query)),
            "result_count": metrics["result_count"],
            "facts_returned": len(facts),
            "rendered_chars": metrics["rendered_context_characters"],
            "recall_mode": recall_mode,
            "latency_ms": latency_ms,
        })

    return {
        "schema": ACTIVE_PREPARE_OUTPUT_SCHEMA,
        "ok": True,
        "context": envelope,
        "metrics": metrics,
    }


def _format_memory_context(envelope: dict[str, Any]) -> str:
    lines = ["NOLLM_MEMORY_CONTEXT_V1"]
    if envelope.get("freshness"):
        lines.append(f"freshness: {envelope['freshness']}")
    if envelope.get("facts"):
        lines.append("facts:")
        for fact in envelope["facts"]:
            lines.append(f"- [{fact.get('kind', 'note')}] {fact.get('claim', '')}")
    if envelope.get("explicit_absences"):
        lines.append("explicit_absences:")
        for absence in envelope["explicit_absences"]:
            lines.append(f"- {absence}")
    if envelope.get("warnings"):
        lines.append("warnings:")
        for warning in envelope["warnings"]:
            lines.append(f"- {warning}")
    lines.append("END_NOLLM_MEMORY_CONTEXT_V1")
    return "\n".join(lines)


def _classify_kind(pattern_name: str, text: str) -> str:
    if pattern_name in ("identity_name", "w_marker_identity", "identity_code"):
        return "identity"
    if pattern_name in ("preference", "w_marker_preference", "response_style_preference"):
        return "preference"
    if pattern_name in ("project_decision", "w_marker_release"):
        return "project"
    facets = analyze_facets(text)
    if "identity_name" in facets or "identity_code" in facets:
        return "identity"
    if "preference_color_or_label" in facets or "preference_response_style" in facets:
        return "preference"
    if "project_release" in facets or "project_decision" in facets:
        return "project"
    return "note"


def _extract_promotion_candidates(messages: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Return list of (kind_hint, text) for user messages that match promotion patterns.

    The full user message is preserved for identity/preference/project/W2 marker
    patterns so that recall queries can match the original marker context. For
    explicit remember directives, only the directive body is promoted.
    """
    candidates: list[tuple[str, str]] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        if msg.get("role") != "user":
            continue
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        for pattern_name, pattern in PROMOTION_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                if pattern_name == "explicit_remember":
                    text = _normalize_text(match.group(1))
                else:
                    text = _normalize_text(content)
                if text:
                    candidates.append((pattern_name, text))
                break
    return candidates


def active_capture(
    native_store_root: Path | str,
    messages: list[dict[str, Any]],
    success: bool,
    trial_id: str | None = None,
    identity: dict[str, str] | None = None,
    trial_root: Path | str | None = None,
) -> dict[str, Any]:
    start = time.monotonic()
    out_dir = _derive_out_dir(native_store_root)

    if not _identity_complete(identity):
        return _active_error("active_identity_incomplete", "agent_id, session_id, and run_id are required for active capture.")

    if not isinstance(success, bool):
        return _active_error("invalid_event", "success must be a boolean.")

    if not isinstance(messages, list):
        return _active_error("invalid_event", "messages must be an array.")

    if len(messages) != 1 or not isinstance(messages[0], dict):
        return _active_error("invalid_event", "active capture requires exactly one current user message.")

    current = messages[0]
    if current.get("role") != "user" or not isinstance(current.get("content"), str):
        return _active_error("invalid_event", "active capture requires one user text message.")

    current_user_message = _normalize_text(current.get("content", ""))
    event_id = _capture_event_id(
        trial_id or "",
        identity.get("agent_id", ""),
        identity.get("session_id", ""),
        identity.get("run_id", ""),
        success,
        current_user_message,
    )

    if trial_id:
        receipt_root = _resolve_trial_root(native_store_root, trial_root)
        claimed, receipt_path = _claim_event_receipt(receipt_root, trial_id, event_id)
        if not claimed:
            return {
                "schema": ACTIVE_CAPTURE_SCHEMA,
                "ok": True,
                "capture": {
                    "event_id": event_id,
                    "promoted_count": 0,
                    "deduplicated_count": 0,
                    "reused_duplicate": True,
                    "suppressed_count": 0,
                    "rejected_count": 0,
                    "records": [],
                },
                "metrics": {
                    "user_messages_seen": 1 if current_user_message else 0,
                    "assistant_messages_ignored": 0,
                    "candidate_count": 0,
                    "latency_ms": int((time.monotonic() - start) * 1000),
                    "replay_observation": True,
                },
            }
    else:
        receipt_path = None

    if not current_user_message:
        if receipt_path is not None:
            _commit_event_receipt(receipt_path, {"promoted_count": 0, "skipped_code": "suppressed_no_current_user_message"})
        return {
            "schema": ACTIVE_CAPTURE_SCHEMA,
            "ok": True,
            "capture": {
                "event_id": event_id,
                "promoted_count": 0,
                "deduplicated_count": 0,
                "suppressed_count": 1,
                "rejected_count": 0,
                "records": [],
                "skipped_code": "suppressed_no_current_user_message",
            },
            "metrics": {
                "user_messages_seen": 0,
                "assistant_messages_ignored": 0,
                "candidate_count": 0,
                "latency_ms": int((time.monotonic() - start) * 1000),
            },
        }

    if not success:
        if receipt_path is not None:
            _commit_event_receipt(receipt_path, {"promoted_count": 0, "skipped_code": "unsuccessful_turn"})
        return {
            "schema": ACTIVE_CAPTURE_SCHEMA,
            "ok": True,
            "capture": {
                "event_id": event_id,
                "promoted_count": 0,
                "deduplicated_count": 0,
                "suppressed_count": 0,
                "rejected_count": 0,
                "records": [],
            },
            "metrics": {
                "user_messages_seen": 0,
                "assistant_messages_ignored": 0,
                "candidate_count": 0,
                "latency_ms": int((time.monotonic() - start) * 1000),
            },
        }

    user_count = 1
    assistant_count = 0

    candidates = _extract_promotion_candidates(messages)
    promoted: list[dict[str, Any]] = []
    deduplicated = 0
    suppressed = 0
    rejected = 0

    for pattern_name, text in candidates:
        if len(text) > 600:
            suppressed += 1
            continue
        if _is_secret(text):
            rejected += 1
            continue
        kind = _classify_kind(pattern_name, text)
        try:
            result = remember_native_memory(
                out_dir, out_dir, out_dir,
                memory=text,
                kind=kind,
                source="active_turn_explicit_v1",
            )
        except CompanionMemoryError as exc:
            if exc.code == "memory_content_too_long":
                suppressed += 1
            elif exc.code == "memory_content_rejected":
                rejected += 1
            else:
                rejected += 1
            continue

        if result.get("ok"):
            if result.get("deduplicated"):
                deduplicated += 1
            else:
                promoted.append({
                    "memory_id": result.get("memory_id", ""),
                    "kind": kind,
                    "source": "active_turn_explicit_v1",
                })
        else:
            rejected += 1

    latency_ms = int((time.monotonic() - start) * 1000)
    if trial_id:
        trial_dir = _ensure_trial_dir(_resolve_trial_root(native_store_root, trial_root), trial_id)
        _write_trial_metric(trial_dir, {
            "event": "capture",
            "timestamp": _now_iso(),
            "trial_id": trial_id,
            "agent_id_hash": _hash_id(identity.get("agent_id", "")) if identity else None,
            "session_id_hash": _hash_id(identity.get("session_id", "")) if identity else None,
            "run_id_hash": _hash_id(identity.get("run_id", "")) if identity else None,
            "event_id": event_id,
            "user_messages_seen": user_count,
            "assistant_messages_ignored": assistant_count,
            "candidate_count": len(candidates),
            "promoted_count": len(promoted),
            "deduplicated_count": deduplicated,
            "reused_duplicate": deduplicated > 0 and len(promoted) == 0,
            "suppressed_count": suppressed,
            "rejected_count": rejected,
            "latency_ms": latency_ms,
        })
        if receipt_path is not None:
            _commit_event_receipt(receipt_path, {
                "promoted_count": len(promoted),
                "deduplicated_count": deduplicated,
                "suppressed_count": suppressed,
                "rejected_count": rejected,
            })
        # Keep a lightweight manifest for operator inspection.
        _update_trial_manifest(trial_dir, {
            "schema": "nollm.active_memory_trial_manifest.v1",
            "trial_id": trial_id,
            "store": "nollm_native_companion",
            "capture_mode": "deterministic_explicit_v1",
            "trial_mode": "active_empirical_v1",
        })

    return {
        "schema": ACTIVE_CAPTURE_SCHEMA,
        "ok": True,
        "capture": {
            "event_id": event_id,
            "promoted_count": len(promoted),
            "deduplicated_count": deduplicated,
            "reused_duplicate": deduplicated > 0 and len(promoted) == 0,
            "suppressed_count": suppressed,
            "rejected_count": rejected,
            "records": promoted,
        },
        "metrics": {
            "user_messages_seen": user_count,
            "assistant_messages_ignored": assistant_count,
            "candidate_count": len(candidates),
            "latency_ms": latency_ms,
        },
    }


def active_trial_report(
    native_store_root: Path | str,
    trial_id: str,
    trial_root: Path | str | None = None,
) -> dict[str, Any]:
    trial_root_path = _resolve_trial_root(native_store_root, trial_root)
    trial_root_dir = trial_root_path / trial_id
    metrics: list[dict[str, Any]] = []
    path = trial_root_dir / "trial-metrics.jsonl"
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    try:
                        metrics.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    prepare_times = [m["latency_ms"] for m in metrics if m.get("event") == "prepare" and isinstance(m.get("latency_ms"), int)]
    capture_times = [m["latency_ms"] for m in metrics if m.get("event") == "capture" and isinstance(m.get("latency_ms"), int)]
    prepare_count = len(prepare_times)
    capture_count = len(capture_times)

    def _pctile(values: list[int], p: float) -> int:
        if not values:
            return 0
        s = sorted(values)
        idx = int((len(s) - 1) * p / 100.0)
        return s[idx]

    return {
        "schema": ACTIVE_TRIAL_REPORT_SCHEMA,
        "ok": True,
        "trial_id": trial_id,
        "prepare_count": prepare_count,
        "capture_count": capture_count,
        "prepare_latency_ms": {
            "p50": _pctile(prepare_times, 50),
            "p95": _pctile(prepare_times, 95),
            "max": max(prepare_times) if prepare_times else 0,
        },
        "capture_latency_ms": {
            "p50": _pctile(capture_times, 50),
            "p95": _pctile(capture_times, 95),
            "max": max(capture_times) if capture_times else 0,
        },
        "metrics_file": str(path) if path.exists() else None,
    }
