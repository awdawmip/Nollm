from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOCS = [
    ROOT / "docs/integration/openclaw/NOLLM_OPENCLAW_RUNTIME_PLUGIN_READINESS_REVIEW.md",
    ROOT / "docs/integration/openclaw/NOLLM_OPENCLAW_SIDECAR_COMMAND_REFERENCE.md",
    ROOT / "docs/integration/openclaw/NOLLM_OPENCLAW_PLUGIN_MAPPING_PROPOSAL.md",
]


def test_openclaw_plugin_readiness_docs_exist_and_cover_commands() -> None:
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)

    for path in DOCS:
        assert path.exists(), path
    for command in ["index", "search", "get", "write-candidate", "status"]:
        assert command in corpus
    for schema_name in ["candidate", "shard", "geometry_mark", "gravity_report", "pending_write"]:
        assert schema_name in corpus


def test_openclaw_plugin_readiness_docs_define_tool_mapping() -> None:
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)

    for tool in [
        "nollm_memory_search",
        "nollm_memory_get",
        "nollm_memory_write_candidate",
        "nollm_memory_status",
    ]:
        assert tool in corpus
    assert "candidate_id" in corpus
    assert "memory_id" in corpus
    assert "shard_id" in corpus
    assert "source_path" in corpus
    assert "line_range" in corpus
    assert "integrations/openclaw/nollm-memory-companion/" in corpus
    assert "npm run plugin:build" in corpus
    assert "npm run plugin:check" in corpus
    assert "npm test" in corpus
    assert "plugins.entries" in corpus


def test_openclaw_plugin_readiness_docs_preserve_boundaries() -> None:
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)
    lower = corpus.lower()

    assert '"real_llm_call": false' in corpus
    assert '"memory_slot_replacement": false' in corpus
    assert '"auto_memory_write": false' in corpus
    assert '"drift_class_trust_mapping": false' in corpus
    assert '"hard_drift_rejection": false' in corpus
    assert "must not\nreplace `memory-core`" in corpus or "must not replace `memory-core`" in corpus
    assert "does not mutate `MEMORY.md`" in corpus
    assert "does not hard-filter by `drift_class`" in corpus
    forbidden_claims = [
        "replaces memory-core",
        "calls a real llm",
        "maps drift_class to trust",
        "maps drift_class to status",
    ]
    for claim in forbidden_claims:
        assert claim not in lower
