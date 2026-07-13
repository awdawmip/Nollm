from __future__ import annotations

import json
import sys

from .adapter import (
    AccessFormationClient, FormationAdapterError, FormationDecisionParser,
    FormationPromptBuilder, FormationResultRenderer, OpenClawEventTranslator,
    OpenClawFormationConfig, formation_schema_bytes, sha256_hex,
)
from .dream_adapter import (
    DREAM_PROMPT_VERSION, build_dream_prompt, dream_schema_bytes,
    process_dream_result, request_from_mapping, sha256_hex as dream_sha256_hex,
)
from .memory_loop import apply_placement, build_placement_prompt, build_recall_prompt, render_recall_injection


def _well_formed(value: object) -> object:
    if isinstance(value, str):
        return value.encode("utf-16", "surrogatepass").decode("utf-16", "replace")
    if isinstance(value, list):
        return [_well_formed(item) for item in value]
    if isinstance(value, dict):
        return {key: _well_formed(item) for key, item in value.items()}
    return value


def _config(envelope: dict[str, object]) -> OpenClawFormationConfig:
    return OpenClawFormationConfig(
        str(envelope["openclaw_command"]), str(envelope["model"]),
        str(envelope.get("prompt_version", "aold-v3")),
        str(envelope.get("schema_version", "aold-formation-v1")),
    )


def main() -> None:
    try:
        envelope = _well_formed(json.load(sys.stdin))
        action = envelope.get("action")
        if action in {"build_dream_prompt", "parse_dream_result"}:
            request = request_from_mapping(envelope["request"])
            if action == "build_dream_prompt":
                version = str(envelope.get("prompt_version", DREAM_PROMPT_VERSION))
                prompt = build_dream_prompt(request, version)
                print(json.dumps({
                    "ok": True, "prompt": prompt, "prompt_version": version,
                    "schema_version": request.schema_version,
                    "prompt_sha256": dream_sha256_hex(prompt.encode("utf-8")),
                    "schema_sha256": dream_sha256_hex(dream_schema_bytes()),
                }, ensure_ascii=True, separators=(",", ":")))
                return
            workspace = envelope.get("statement_store_workspace")
            result = process_dream_result(
                str(envelope["raw_model_response"]), request, str(envelope["result_id"]),
                None if workspace is None else __import__("pathlib").Path(str(workspace)),
            )
            print(json.dumps({"ok": True, **result}, ensure_ascii=True, separators=(",", ":")))
            return
        if action == "build_placement_prompt":
            result = build_placement_prompt(envelope["statement"], envelope["session_key"], envelope["memory_workspace"], envelope["request_id"])
            print(json.dumps({"ok": True, **result}, ensure_ascii=True, separators=(",", ":")))
            return
        if action == "apply_placement":
            result = apply_placement(envelope["raw_model_response"], envelope["statement"], envelope["session_key"], envelope["memory_workspace"], envelope["request_id"])
            print(json.dumps({"ok": True, **result}, ensure_ascii=True, separators=(",", ":")))
            return
        if action == "build_recall_prompt":
            result = build_recall_prompt(envelope["query"], envelope["session_key"], envelope["memory_workspace"], envelope["request_id"])
            print(json.dumps({"ok": True, **result}, ensure_ascii=True, separators=(",", ":")))
            return
        if action == "render_recall_injection":
            result = render_recall_injection(envelope["raw_model_response"], envelope["candidates"])
            print(json.dumps({"ok": True, **result}, ensure_ascii=True, separators=(",", ":")))
            return
        request = OpenClawEventTranslator().translate(envelope["request"])
        config = _config(envelope)
        if action == "build_prompt":
            prompt = FormationPromptBuilder().build(request, config, envelope.get("retry_error"))
            print(json.dumps({
                "ok": True, "prompt": prompt,
                "prompt_version": config.prompt_version, "schema_version": config.schema_version,
                "prompt_sha256": sha256_hex(prompt.encode("utf-8")),
                "schema_sha256": sha256_hex(formation_schema_bytes(config)),
            }, ensure_ascii=True, separators=(",", ":")))
            return
        if action != "parse_result":
            raise FormationAdapterError("invalid_action", "action must be build_prompt or parse_result")
        decision = FormationDecisionParser().parse(str(envelope["raw_model_response"]), request, config, str(envelope["decision_id"]))
        statements = AccessFormationClient().form(request, decision)
        result = FormationResultRenderer().render(request, decision, statements)
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=True, separators=(",", ":")))
    except (KeyError, TypeError, ValueError, FormationAdapterError) as exc:
        print(json.dumps({"ok": False, "error": getattr(exc, "category", "invalid_input"), "message": str(exc)}, ensure_ascii=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
