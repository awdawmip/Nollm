from __future__ import annotations

import json
from pathlib import Path
import tempfile

from nollm.grf.facade import GRFFacade


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nollm-grf8-ingestion-") as temp:
        root = Path(temp)
        files = {"notes.md": "# Project\nconstraint\n\n## Revision\nlatest", "notes.txt": "plain retained text", "facts.json": '{"fact":"one","kind":"json"}', "facts.jsonl": '{"fact":"one"}\n{"fact":"two"}\n', "code.py": "def f():\n    return 1\n\ndef g():\n    return 2\n", "chat.log": "user: decide\n\nassistant: recorded"}
        for name, content in files.items(): (root / name).write_text(content, encoding="utf-8")
        facade = GRFFacade(root / "workspace")
        ingested = {name: facade.capture_source(root / name, "2026-07-11T00:00:00Z") for name in files}
        repeated = facade.capture_source(root / "notes.md", "2026-07-11T00:00:01Z")
        result = {"source_count": len(ingested), "shard_count": sum(len(item.created_shards) for item in ingested.values()), "idempotent_reload": repeated.unchanged, "source_fallback": all(facade.get_source(shard) for item in ingested.values() for shard in item.created_shards)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["idempotent_reload"] and result["source_fallback"] else 1


if __name__ == "__main__": raise SystemExit(main())
