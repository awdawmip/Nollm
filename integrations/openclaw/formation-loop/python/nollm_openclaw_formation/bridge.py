from __future__ import annotations

import json
import os
import sys

from .adapter import AccessFormationClient, FormationAdapterError, FormationDecisionParser, FormationResultRenderer, OpenClawEventTranslator, OpenClawFormationConfig


def main() -> None:
    try:
        envelope = json.load(sys.stdin)
        request = OpenClawEventTranslator().translate(envelope["request"])
        config = OpenClawFormationConfig(envelope["openclaw_command"], envelope["model"])
        decision = FormationDecisionParser().parse(envelope["raw_model_response"], request, config, envelope["decision_id"])
        statements = AccessFormationClient().form(request, decision)
        result = FormationResultRenderer().render(request, decision, statements)
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, separators=(",", ":")))
    except (KeyError, TypeError, ValueError, FormationAdapterError) as exc:
        print(json.dumps({"ok": False, "error": getattr(exc, "category", "invalid_input"), "message": str(exc)}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
