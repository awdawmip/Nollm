"""Nollm native active memory provider for OpenClaw Functional Alpha.
This module implements the Python side of the F0-01 memory provider.
It is intentionally isolated from legacy memory surfaces:
  - no MEMORY.md / DREAMS.md / memory/*.md reads or writes
  - no legacy workspace parsing
  - deterministic synthetic alpha field only
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ALPHA_FIELD_SCHEMA = "nollm.alpha_field.v1"
PREPARE_SCHEMA = "nollm.provider.prepare.v1"
PREPARE_RESULT_SCHEMA = "nollm.provider.prepare_result.v1"
CAPTURE_SCHEMA = "nollm.provider.capture.v2"
CAPTURE_RESULT_SCHEMA = "nollm.provider.capture_result.v1"
MEMORY_CONTEXT_SCHEMA = "nollm.memory_context.v1"

LEGACY_SEGMENTS = {"memory", "memory.md", "dreams.md", "legacy_workspace", "legacy-workspace"}


class NollmProviderError(Exception):
    """Structured error for the provider alpha."""

    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable

    def to_record(self) -> dict[str, object]:
        return {
            "ok": False,
            "schema": "nollm.provider.error.v1",
            "error": {
                "code": self.code,
                "message": self.message,
                "retryable": self.retryable,
            },
        }


def _stable_json(data: object, sort_keys: bool = True) -> str:
    """Canonical compact JSON with sorted keys."""
    return json.dumps(data, sort_keys=sort_keys, separators=(",", ":"), ensure_ascii=False)


def _sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _is_path_under_legacy(path: Path) -> bool:
    """Fail-close if nollmDataRoot appears to live inside legacy memory paths."""
    s = str(path).replace(chr(92), "/").lower()
    parts = [p for p in s.split("/") if p]
    for part in parts:
        if part in LEGACY_SEGMENTS:
            return True
    import os
    basename = os.path.splitext(parts[-1] if parts else "")[0]
    if basename in LEGACY_SEGMENTS:
        return True
    return False


def _validate_absolute_directory(path: str | Path, name: str) -> Path:
    value = Path(path)
    if not value.is_absolute():
        raise NollmProviderError(
            "configuration_error",
            f"{name} must be an absolute path: {path}",
            retryable=False,
        )
    return value


@dataclass(frozen=True)
class AlphaFact:
    shard_id: str
    claim: str
    keywords: tuple[str, ...]
    epistemic_state: str
    operational_state: str
    source_refs: tuple[str, ...]

    def to_record(self) -> dict[str, object]:
        return {
            "shard_id": self.shard_id,
            "claim": self.claim,
            "keywords": list(self.keywords),
            "epistemic_state": self.epistemic_state,
            "operational_state": self.operational_state,
            "source_refs": list(self.source_refs),
        }


@dataclass(frozen=True)
class AlphaField:
    field_id: str
    revision_id: str
    facts: tuple[AlphaFact, ...]
    source_path: Path

    @classmethod
    def load(cls, fixture_path: str | Path) -> "AlphaField":
        path = Path(fixture_path)
        if not path.is_absolute():
            raise NollmProviderError(
                "configuration_error",
                f"alphaFixturePath must be absolute: {fixture_path}",
                retryable=False,
            )
        if not path.is_file():
            raise NollmProviderError(
                "field_unavailable",
                f"alpha fixture not found: {fixture_path}",
                retryable=True,
            )

        try:
            raw_text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise NollmProviderError(
                "field_unavailable",
                f"cannot read alpha fixture: {exc}",
                retryable=True,
            ) from exc

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise NollmProviderError(
                "field_malformed",
                f"alpha fixture is not valid JSON: {exc}",
                retryable=False,
            ) from exc

        return cls._from_payload(payload, path)

    @classmethod
    def _from_payload(cls, payload: dict[str, object], source_path: Path) -> "AlphaField":
        if not isinstance(payload, dict):
            raise NollmProviderError(
                "field_malformed", "alpha fixture must be a JSON object", retryable=False
            )
        schema = payload.get("schema")
        if schema != ALPHA_FIELD_SCHEMA:
            raise NollmProviderError(
                "field_malformed",
                f"unsupported alpha field schema: {schema!r}",
                retryable=False,
            )
        field_id = payload.get("field_id")
        if not isinstance(field_id, str) or not field_id:
            raise NollmProviderError(
                "field_malformed", "field_id must be a non-empty string", retryable=False
            )
        revision_id = payload.get("revision_id")
        if not isinstance(revision_id, str) or not revision_id:
            raise NollmProviderError(
                "field_malformed",
                "revision_id must be a non-empty string",
                retryable=False,
            )

        raw_facts = payload.get("facts")
        if not isinstance(raw_facts, list):
            raise NollmProviderError(
                "field_malformed", "facts must be a list", retryable=False
            )

        facts: list[AlphaFact] = []
        for index, raw in enumerate(raw_facts):
            if not isinstance(raw, dict):
                raise NollmProviderError(
                    "field_malformed",
                    f"fact[{index}] must be an object",
                    retryable=False,
                )
            facts.append(cls._parse_fact(raw, index))

        field = cls(
            field_id=field_id,
            revision_id=revision_id,
            facts=tuple(facts),
            source_path=source_path,
        )
        computed = field.compute_revision_id()
        if computed != revision_id:
            raise NollmProviderError(
                "field_malformed",
                f"revision_id mismatch: expected {computed}, got {revision_id}",
                retryable=False,
            )
        return field

    @staticmethod
    def _parse_fact(raw: dict[str, object], index: int) -> AlphaFact:
        shard_id = raw.get("shard_id")
        if not isinstance(shard_id, str) or not shard_id:
            raise NollmProviderError(
                "field_malformed",
                f"fact[{index}].shard_id must be a non-empty string",
                retryable=False,
            )
        claim = raw.get("claim")
        if not isinstance(claim, str) or not claim:
            raise NollmProviderError(
                "field_malformed",
                f"fact[{index}].claim must be a non-empty string",
                retryable=False,
            )
        keywords = raw.get("keywords")
        if not isinstance(keywords, list) or not all(
            isinstance(k, str) and k for k in keywords
        ):
            raise NollmProviderError(
                "field_malformed",
                f"fact[{index}].keywords must be a list of non-empty strings",
                retryable=False,
            )
        epistemic_state = raw.get("epistemic_state")
        if not isinstance(epistemic_state, str) or not epistemic_state:
            raise NollmProviderError(
                "field_malformed",
                f"fact[{index}].epistemic_state must be a non-empty string",
                retryable=False,
            )
        operational_state = raw.get("operational_state")
        if not isinstance(operational_state, str) or not operational_state:
            raise NollmProviderError(
                "field_malformed",
                f"fact[{index}].operational_state must be a non-empty string",
                retryable=False,
            )
        source_refs = raw.get("source_refs")
        if not isinstance(source_refs, list) or not all(
            isinstance(ref, str) and ref for ref in source_refs
        ):
            raise NollmProviderError(
                "field_malformed",
                f"fact[{index}].source_refs must be a list of non-empty strings",
                retryable=False,
            )
        return AlphaFact(
            shard_id=shard_id,
            claim=claim,
            keywords=tuple(str(k) for k in keywords),
            epistemic_state=epistemic_state,
            operational_state=operational_state,
            source_refs=tuple(str(ref) for ref in source_refs),
        )

    def compute_revision_id(self) -> str:
        """Deterministic revision identity from canonical field data."""
        canonical: dict[str, object] = {
            "schema": ALPHA_FIELD_SCHEMA,
            "field_id": self.field_id,
            "facts": [fact.to_record() for fact in self.facts],
        }
        return _sha256_hex(_stable_json(canonical))


class ProviderConfig:
    """Validated runtime configuration for the F0 provider."""

    def __init__(
        self,
        python_command: str,
        nollm_repo_root: Path,
        nollm_data_root: Path,
        alpha_fixture_path: Path,
        command_timeout_ms: int,
        max_facts: int,
        max_characters: int,
        capture_mode: str,
    ) -> None:
        self.python_command = python_command
        self.nollm_repo_root = nollm_repo_root
        self.nollm_data_root = nollm_data_root
        self.alpha_fixture_path = alpha_fixture_path
        self.command_timeout_ms = command_timeout_ms
        self.max_facts = max_facts
        self.max_characters = max_characters
        self.capture_mode = capture_mode

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> "ProviderConfig":
        if not isinstance(payload, dict):
            raise NollmProviderError(
                "configuration_error", "config must be an object", retryable=False
            )
        python_command = payload.get("pythonCommand", "python3")
        if not isinstance(python_command, str) or not python_command:
            raise NollmProviderError(
                "configuration_error",
                "pythonCommand must be a non-empty string",
                retryable=False,
            )

        nollm_repo_root = _validate_absolute_directory(
            payload.get("nollmRepoRoot", ""), "nollmRepoRoot"
        )
        nollm_data_root = _validate_absolute_directory(
            payload.get("nollmDataRoot", ""), "nollmDataRoot"
        )
        alpha_fixture_path = _validate_absolute_directory(
            payload.get("alphaFixturePath", ""), "alphaFixturePath"
        )

        # D5: fixture containment - alphaFixturePath must be under nollmRepoRoot
        try:
            nollm_repo_root.resolve().joinpath(alpha_fixture_path.resolve().relative_to(nollm_repo_root.resolve()))
        except ValueError:
            raise NollmProviderError(
                "configuration_error",
                "alphaFixturePath must be under nollmRepoRoot",
                retryable=False,
            ) from None

        if _is_path_under_legacy(nollm_data_root):
            raise NollmProviderError(
                "configuration_error",
                "nollmDataRoot must not be inside a legacy memory path",
                retryable=False,
            )

        timeout_ms = payload.get("commandTimeoutMs", 15000)
        if not isinstance(timeout_ms, int) or timeout_ms < 1000 or timeout_ms > 60000:
            raise NollmProviderError(
                "configuration_error",
                "commandTimeoutMs must be an integer between 1000 and 60000",
                retryable=False,
            )
        max_facts = payload.get("maxFacts", 3)
        if not isinstance(max_facts, int) or max_facts < 1 or max_facts > 20:
            raise NollmProviderError(
                "configuration_error",
                "maxFacts must be an integer between 1 and 20",
                retryable=False,
            )
        max_characters = payload.get("maxCharacters", 1200)
        if not isinstance(max_characters, int) or max_characters < 100 or max_characters > 10000:
            raise NollmProviderError(
                "configuration_error",
                "maxCharacters must be an integer between 100 and 10000",
                retryable=False,
            )
        capture_mode = payload.get("captureMode", "receipt_only")
        if capture_mode != "receipt_only":
            raise NollmProviderError(
                "configuration_error",
                f"unsupported captureMode: {capture_mode}",
                retryable=False,
            )

        return cls(
            python_command=python_command,
            nollm_repo_root=nollm_repo_root,
            nollm_data_root=nollm_data_root,
            alpha_fixture_path=alpha_fixture_path,
            command_timeout_ms=timeout_ms,
            max_facts=max_facts,
            max_characters=max_characters,
            capture_mode=capture_mode,
        )


def _extract_last_user_text(messages: list[dict[str, object]]) -> str:
    """Extract the most recent user-visible text from the turn messages."""
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")
        if role == "user" and isinstance(content, str):
            return content
        if role == "user" and isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    parts.append(str(part["text"]))
            if parts:
                return "\n".join(parts)
    return ""


def _keyword_match(query: str, facts: Iterable[AlphaFact]) -> list[AlphaFact]:
    """Simple deterministic keyword selection for F0."""
    tokens = {token.lower() for token in re.split(r"[^a-zA-Z0-9_-]+", query) if token}
    if not tokens:
        return []
    scored: list[tuple[int, AlphaFact]] = []
    for fact in facts:
        keywords = {kw.lower() for kw in fact.keywords}
        score = len(tokens & keywords)
        if score > 0:
            scored.append((score, fact))
    scored.sort(key=lambda item: (-item[0], item[1].shard_id))
    return [fact for _, fact in scored]


def _make_context_id(run_id: str) -> str:
    return _sha256_hex(_stable_json({"run_id": run_id}))


def prepare(
    field: AlphaField,
    payload: dict[str, object],
    config: ProviderConfig,
) -> dict[str, object]:
    """Handle a prepare command and return a bounded NOLLM_MEMORY_CONTEXT_V1."""
    schema = payload.get("schema")
    if schema != PREPARE_SCHEMA:
        raise NollmProviderError(
            "invalid_command",
            f"expected schema {PREPARE_SCHEMA}, got {schema!r}",
            retryable=False,
        )
    run_id = payload.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise NollmProviderError(
            "invalid_command", "run_id must be a non-empty string", retryable=False
        )

    messages = payload.get("messages", [])
    if not isinstance(messages, list):
        raise NollmProviderError(
            "invalid_command", "messages must be a list", retryable=False
        )
    typed_messages = [m for m in messages if isinstance(m, dict)]
    query = _extract_last_user_text(typed_messages)

    budget = payload.get("budget", {})
    if not isinstance(budget, dict):
        budget = {}
    max_facts = budget.get("max_facts", config.max_facts)
    max_characters = budget.get("max_characters", config.max_characters)
    if not isinstance(max_facts, int) or max_facts < 1:
        max_facts = config.max_facts
    if not isinstance(max_characters, int) or max_characters < 1:
        max_characters = config.max_characters

    matched = _keyword_match(query, field.facts)
    matched = matched[:max_facts]

    facts_json: list[dict[str, object]] = []
    total_chars = 0
    for fact in matched:
        record = fact.to_record()
        record_chars = len(str(record))
        if total_chars + record_chars > max_characters and facts_json:
            break
        facts_json.append(record)
        total_chars += record_chars

    freshness = "fresh" if facts_json else "none"
    explicit_absences: list[str] = []
    if not facts_json:
        explicit_absences.append(
            "No matching active Nollm memory was found in the Functional Alpha field."
        )

    context = {
        "schema": MEMORY_CONTEXT_SCHEMA,
        "context_id": _make_context_id(run_id),
        "field_id": field.field_id,
        "field_revision_id": field.revision_id,
        "freshness": freshness,
        "facts": facts_json,
        "boundaries": [
            {
                "scope": "functional_alpha",
                "source": "synthetic_fixture",
                "max_facts_applied": config.max_facts,
                "max_characters_applied": config.max_characters,
            }
        ],
        "warnings": [],
        "completeness": {
            "mode": "bounded",
            "explicit_absences": explicit_absences,
        },
    }

    return {
        "ok": True,
        "schema": PREPARE_RESULT_SCHEMA,
        "context": context,
    }


def _canonical_event_hash(
    agent_id: str,
    session_id: str,
    run_id: str,
    success: bool,
    messages: list[dict[str, object]],
    field_id: str,
    field_revision_id: str,
) -> str:
    """D4: Python is the sole canonical capture identity authority.
    The canonical event includes all durable identity fields, the field
    revision, and the capture protocol version."""
    return _sha256_hex(
        _stable_json({
            "agent_id": agent_id,
            "session_id": session_id,
            "run_id": run_id,
            "success": success,
            "messages": messages,
            "field_id": field_id,
            "field_revision_id": field_revision_id,
            "capture_protocol_version": "nollm.capture_identity.v2",
        })
    )


def _sanitize_messages(messages: list[dict[str, object]]) -> list[dict[str, object]]:
    """Recursively redact secrets and credentials from capture messages.

    F0 default capture_mode is receipt_only: we store only role, content hash,
    content length, and a bounded safe summary. Raw message bodies are not
    persisted. This function is still applied as defense-in-depth.
    """
    secret_keys = {"api_key", "apikey", "token", "password", "secret", "authorization"}
    secret_patterns = re.compile(
        r"(?i)(api[_-]?key|token|password|secret|authorization|bearer)\s*[:=]\s*\S+",
    )

    def _redact_value(value: object) -> object:
        if isinstance(value, dict):
            return {k: ("<redacted>" if any(sk in str(k).lower() for sk in secret_keys) else _redact_value(v)) for k, v in value.items()}
        if isinstance(value, list):
            return [_redact_value(item) for item in value]
        if isinstance(value, str):
            return secret_patterns.sub(lambda m: m.group(0).split("=")[0].split(":")[0] + "=<redacted>", value)
        return value

    result: list[dict[str, object]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        copy: dict[str, object] = {}
        for key, value in message.items():
            lower_key = str(key).lower()
            if any(sk in lower_key for sk in secret_keys):
                copy[key] = "<redacted>"
            else:
                copy[key] = _redact_value(value)
        result.append(copy)
    return result


def capture(
    field: AlphaField,
    payload: dict[str, object],
    config: ProviderConfig,
) -> dict[str, object]:
    """Handle a capture command and write a durable receipt under nollmDataRoot.

    D4: Python is the sole canonical capture identity authority. TS forwards a
    strict minimal event; Python validates, computes the canonical event hash,
    and returns the canonical receipt_id. No caller event_hash is accepted.
    """
    schema = payload.get("schema")
    if schema != CAPTURE_SCHEMA:
        raise NollmProviderError(
            "invalid_command",
            f"expected schema {CAPTURE_SCHEMA}, got {schema!r}",
            retryable=False,
        )

    # D4: strict identity validation
    agent_id = payload.get("agent_id", "")
    session_id = payload.get("session_id", "")
    run_id = payload.get("run_id", "")
    for name, value in [("agent_id", agent_id), ("session_id", session_id), ("run_id", run_id)]:
        if not isinstance(value, str) or not value:
            raise NollmProviderError(
                "invalid_command",
                f"{name} must be a non-empty string",
                retryable=False,
            )

    # D4: strict success validation - no silent default
    success = payload.get("success")
    if not isinstance(success, bool):
        raise NollmProviderError(
            "invalid_command",
            "success must be a boolean",
            retryable=False,
        )

    # D4: strict messages validation - must be a list
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise NollmProviderError(
            "invalid_command",
            "messages must be a list",
            retryable=False,
        )
    typed_messages = [m for m in messages if isinstance(m, dict)]

    # D4: Canonical event hash computed solely by Python
    event_hash = _canonical_event_hash(
        agent_id=agent_id,
        session_id=session_id,
        run_id=run_id,
        success=success,
        messages=typed_messages,
        field_id=field.field_id,
        field_revision_id=field.revision_id,
    )

    receipt_id = _sha256_hex(
        _stable_json({
            "agent_id": agent_id,
            "session_id": session_id,
            "run_id": run_id,
            "success": success,
            "canonical_event_hash": event_hash,
            "field_id": field.field_id,
            "field_revision_id": field.revision_id,
            "capture_protocol_version": "nollm.capture_identity.v2",
        })
    )

    # receipt_only mode: store only structural metadata, not raw content
    message_summaries: list[dict[str, object]] = []
    if success:
        for msg in _sanitize_messages(typed_messages):
            role = msg.get("role", "unknown")
            msg_content = msg.get("content", "")
            if isinstance(msg_content, str):
                content_hash = _sha256_hex(msg_content.encode("utf-8"))
                content_length = len(msg_content)
            elif isinstance(msg_content, list):
                content_json = _stable_json(msg_content)
                content_hash = _sha256_hex(content_json.encode("utf-8"))
                content_length = len(content_json)
            else:
                content_hash = _sha256_hex(str(msg_content).encode("utf-8"))
                content_length = len(str(msg_content))
            message_summaries.append({
                "role": role,
                "content_hash": content_hash,
                "content_length": content_length,
            })

    receipt_payload = {
        "schema": "nollm.capture_receipt.v2",
        "receipt_id": receipt_id,
        "canonical_event_hash": event_hash,
        "run_id": run_id,
        "success": success,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "field_id": field.field_id,
        "field_revision_id": field.revision_id,
        "legacy_memory_mutated": False,
        "message_summaries": message_summaries,
    }

    receipt_dir = config.nollm_data_root / "functional-alpha" / "capture-receipts"
    receipt_path = receipt_dir / f"{receipt_id}.json"

    try:
        receipt_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise NollmProviderError(
            "capture_failed",
            f"failed to create receipt directory: {exc}",
            retryable=True,
        ) from exc

    receipt_bytes = _stable_json(receipt_payload, sort_keys=True).encode("utf-8")

    # D5: Atomic no-clobber publish. Try to create the final file with O_EXCL
    # so concurrent duplicate events produce exactly one creator; all others
    # fall through to the reuse path.
    try:
        fd = os.open(str(receipt_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        # Another caller created the receipt in the race window; reuse below.
        fd = None
    except OSError as exc:
        raise NollmProviderError(
            "capture_failed",
            f"failed to open capture receipt: {exc}",
            retryable=True,
        ) from exc

    if fd is not None:
        try:
            with os.fdopen(fd, "wb") as tmp_f:
                tmp_f.write(receipt_bytes)
        except OSError as exc:
            # Best-effort cleanup of partially written file
            try:
                receipt_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise NollmProviderError(
                "capture_failed",
                f"failed to write capture receipt: {exc}",
                retryable=True,
            ) from exc
        return {
            "ok": True,
            "schema": CAPTURE_RESULT_SCHEMA,
            "reused": False,
            "receipt": {
                "receipt_id": receipt_id,
                "event_hash": event_hash,
                "stored_at": str(receipt_path),
                "state": "captured_pending_native_ingress",
                "legacy_memory_mutated": False,
            },
        }

    # D5: Receipt already exists. Validate expected identity; quarantine corrupt files.
    # Retry briefly only when the file is empty, which tolerates the race between
    # a concurrent creator opening the file and finishing the write.
    existing: dict[str, object] | None = None
    existing_raw = ""
    for attempt in range(10):
        try:
            existing_raw = receipt_path.read_text(encoding="utf-8")
            if not existing_raw.strip():
                time.sleep(0.005)
                continue
            existing = json.loads(existing_raw)
            break
        except json.JSONDecodeError:
            # Non-empty but malformed: treat as corrupt immediately.
            break
        except Exception:
            time.sleep(0.005)

    if existing is None:
        # Move corrupt receipt to quarantine and fail closed
        quarantine_dir = receipt_dir / "quarantine"
        try:
            quarantine_dir.mkdir(parents=True, exist_ok=True)
            quarantine_path = quarantine_dir / f"{receipt_id}-{int(time.time())}.json"
            receipt_path.rename(quarantine_path)
        except OSError:
            pass
        raise NollmProviderError(
            "capture_failed",
            f"corrupt existing receipt quarantined, no overwrite: {'empty file' if not existing_raw.strip() else 'invalid json'}",
            retryable=False,
        ) from None

    existing_event_hash = existing.get("canonical_event_hash") or existing.get("event_hash")
    if existing_event_hash == event_hash:
        return {
            "ok": True,
            "schema": CAPTURE_RESULT_SCHEMA,
            "reused": True,
            "receipt": {
                "receipt_id": receipt_id,
                "event_hash": event_hash,
                "stored_at": str(receipt_path),
                "state": "captured_pending_native_ingress",
                "legacy_memory_mutated": False,
            },
        }
    raise NollmProviderError(
        "capture_failed",
        f"receipt collision: {receipt_id} exists with different content",
        retryable=False,
    )


def status(field: AlphaField | None, config: ProviderConfig) -> dict[str, object]:
    """Return a compatibility/status summary."""
    return {
        "ok": True,
        "schema": "nollm.provider.status.v1",
        "provider": "nollm",
        "backend_kind": "nollm",
        "compatibility_shim": True,
        "field_id": field.field_id if field else None,
        "field_revision_id": field.revision_id if field else None,
        "freshness": "fresh" if field else "unavailable",
        "data_root": str(config.nollm_data_root),
    }


def dispatch(
    command: str,
    payload: dict[str, object],
    config: ProviderConfig,
    field: AlphaField | None,
) -> dict[str, object]:
    """Dispatch stdin JSON commands to handler functions."""
    if command == "status":
        return status(field, config)
    if field is None:
        raise NollmProviderError(
            "field_unavailable",
            "alpha field is not available",
            retryable=True,
        )
    if command == "prepare":
        return prepare(field, payload, config)
    if command == "capture":
        return capture(field, payload, config)
    raise NollmProviderError(
        "invalid_command",
        f"unknown command: {command}",
        retryable=False,
    )


def run_from_stdin(config_payload: dict[str, object]) -> dict[str, object]:
    """Read one command object from stdin and return the result record."""
    try:
        config = ProviderConfig.from_payload(config_payload)
    except NollmProviderError as exc:
        return exc.to_record()

    try:
        raw_stdin = sys.stdin.read()
    except OSError as exc:
        return NollmProviderError(
            "sidecar_failed",
            f"failed to read stdin: {exc}",
            retryable=True,
        ).to_record()

    if not raw_stdin.strip():
        return NollmProviderError(
            "invalid_command",
            "empty stdin",
            retryable=False,
        ).to_record()

    try:
        command_payload = json.loads(raw_stdin)
    except json.JSONDecodeError as exc:
        return NollmProviderError(
            "invalid_command",
            f"stdin is not valid JSON: {exc}",
            retryable=False,
        ).to_record()

    if not isinstance(command_payload, dict):
        return NollmProviderError(
            "invalid_command",
            "stdin JSON must be an object",
            retryable=False,
        ).to_record()

    command = command_payload.get("command")
    if not isinstance(command, str) or not command:
        return NollmProviderError(
            "invalid_command",
            "command must be a non-empty string",
            retryable=False,
        ).to_record()

    field: AlphaField | None = None
    try:
        field = AlphaField.load(config.alpha_fixture_path)
    except NollmProviderError as exc:
        if command != "status":
            return exc.to_record()

    try:
        return dispatch(command, command_payload, config, field)
    except NollmProviderError as exc:
        return exc.to_record()
