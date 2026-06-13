# Terminology

This file is the canonical terminology contract for Nollm protocol text, examples, and machine namespaces.

## Project and Example Names

| Concept | Canonical term | Machine form | Do not use |
|---|---|---|---|
| Nollm project | Nollm | nollm | NOLLM as a separate acronym unless referring to package names |
| OpenClaw example/project | OpenClaw | openclaw | Obsolete example namespace or informal Chinese nicknames |

Rules:

- Use `OpenClaw` as the display name.
- Use `openclaw` as the machine namespace.
- Use `examples/openclaw/` for the example notebook.
- Use `nollm://openclaw/...` for memory addresses.
- Do not reintroduce obsolete project nicknames or namespaces guarded by `reference/python/tests/test_terminology.py`.

## Forbidden Terms

The following obsolete terms may appear only in this section as regression-test fixtures:

- `lobster`
- `Lobster`
- `LOBSTER`
- `榫欒櫨`
- `榫嶈潶`
- `nollm://lobster`
- `examples/lobster`

## Architecture Terms

| English | Chinese | Notes |
|---|---|---|
| Anchor Field | 锚场 | Prefer this over bare "anchor" when discussing architecture. |
| Anchor Column Field | 柱状锚场 | Cross-layer semantic field. |
| Layered Rotating Honeycomb Memory Field | 分层旋转蜂巢记忆场 | Spatial architecture. |
| Scale Scan | 尺度扫描 | Recall mechanism; not tree descent. |
| Lateral Recovery | 横向纠偏 | Recovery across overlapping anchor fields. |
| Recall Digest | 召回摘要 | Compact context payload. |
| Audit Projection | 审计投影 | SQLite role only. |

## Anti-Terms

Do not describe Nollm as:

- a directory tree;
- a vector database;
- a knowledge graph;
- a RAG engine;
- a database-centered memory engine;
- an autonomous agent runtime.

Keep these architecture phrases stable:

- Anchor is Field, not Folder.
- Recall is Scale Scan, not Tree Descent.
- Layered Rotating Honeycomb Memory Field.
- SQLite is Audit Projection, not Memory.
