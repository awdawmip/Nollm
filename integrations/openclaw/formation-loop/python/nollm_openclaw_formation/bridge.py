from __future__ import annotations

import json
import sys

from .adapter import (
    AccessFormationClient, FormationAdapterError, FormationDecisionParser,
    FormationPromptBuilder, FormationResultRenderer, OpenClawEventTranslator,
    OpenClawFormationConfig, formation_schema_bytes, sha256_hex,
)


def _config(envelope: dict[str, object]) -> OpenClawFormationConfig:
    return OpenClawFormationConfig(
        str(envelope["openclaw_command"]), str(envelope["model"]),
        str(envelope.get("prompt_version", "aold-v3")),
        str(envelope.get("schema_version", "aold-formation-v1")),
    )


def main() -> None:
    try:
        envelope = json.load(sys.stdin)
        request = OpenClawEventTranslator().translate(envelope["request"])
        config = _config(envelope)
        action = envelope.get("action")
        if action == "build_prompt":
            prompt = FormationPromptBuilder().build(request, config, envelope.get("retry_error"))
            print(json.dumps({
                "ok": True, "prompt": prompt,
                "prompt_version": config.prompt_version, "schema_version": config.schema_version,
                "prompt_sha256": sha256_hex(prompt.encode("utf-8")),
                "schema_sha256": sha256_hex(formation_schema_bytes(config)),
            }, ensure_ascii=False, separators=(",", ":")))
            return
        if action != "parse_result":
            raise FormationAdapterError("invalid_action", "action must be build_prompt or parse_result")
        decision = FormationDecisionParser().parse(str(envelope["raw_model_response"]), request, config, str(envelope["decision_id"]))
        statements = AccessFormationClient().form(request, decision)
        result = FormationResultRenderer().render(request, decision, statements)
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, separators=(",", ":")))
    except (KeyError, TypeError, ValueError, FormationAdapterError) as exc:
        print(json.dumps({"ok": False, "error": getattr(exc, "category", "invalid_input"), "message": str(exc)}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
