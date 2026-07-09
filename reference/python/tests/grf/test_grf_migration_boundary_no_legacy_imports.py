from __future__ import annotations

import ast
from pathlib import Path

from nollm.grf.importers import import_v2_dream_shard_like


ROOT = Path(__file__).resolve().parents[4]
IMPORTERS = ROOT / "reference" / "python" / "nollm" / "grf" / "importers.py"


def test_importers_do_not_import_legacy_or_runtime_packages() -> None:
    tree = ast.parse(IMPORTERS.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    forbidden = ("hcg", "hag", "hx", "oca", "openclaw", "dream_geometry", "integrations")
    assert not [name for name in imported if any(part in name.lower() for part in forbidden)]


def test_dream_shard_like_import_preserves_explicit_shard_id_without_geometry() -> None:
    shard = import_v2_dream_shard_like(
        {
            "shard_id": "shard:v2:explicit",
            "content": "dream shard content",
            "created_at": "2026-07-09T00:00:00Z",
            "origin_kind": "validation_fixture",
            "source_window_refs": ["source:v2:ctx"],
        }
    )
    payload = shard.to_mapping()
    assert shard.shard_id == "shard:v2:explicit"
    assert payload["content"] == "dream shard content"
    assert "geometry_mark" not in payload
    assert "placement" not in payload
