from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOCS = [
    ROOT / "docs/integration/openclaw/NOLLM_OPENCLAW_MEMORY_ADAPTER_DESIGN.md",
    ROOT / "docs/integration/openclaw/NOLLM_OPENCLAW_MEMORY_TOOL_CONTRACT.md",
    ROOT / "docs/integration/openclaw/NOLLM_OPENCLAW_LLM_USAGE_GUIDE.md",
    ROOT / "docs/integration/openclaw/NOLLM_OPENCLAW_MEMORY_LLM_PROMPT.md",
]
FIXTURE = ROOT / "examples/openclaw_memory_fixture"


def test_openclaw_memory_adapter_docs_exist_and_set_boundaries() -> None:
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in DOCS)

    for path in DOCS:
        assert path.exists(), path
    # F0-02: Nollm provider is the active memory source, not legacy companion
    assert "active memory provider" in corpus.lower()
    assert "private recall" in corpus.lower()
    assert "private capture" in corpus.lower()
    assert "NOLLM_MEMORY_CONTEXT_V1" in corpus
    # Legacy files are not used for active recall
    assert "not read or written" in corpus.lower()
    # Companion mode is historical, not the active path
    assert "companion tool mode" in corpus.lower()
    # drift_class must not map to trust/status
    assert "Do not map `drift_class` to trust/status" in corpus


def test_openclaw_memory_adapter_docs_avoid_forbidden_claims() -> None:
    corpus = "\n".join(path.read_text(encoding="utf-8").lower() for path in DOCS)

    forbidden = [
        "nollm replaces vector db",
        "solves long-term memory",
        "drift_class maps to trust",
        "drift_class maps to status",
        "automatic durable writeback",
        "real llm call",
    ]
    for phrase in forbidden:
        assert phrase not in corpus


def test_openclaw_memory_fixture_exists() -> None:
    required = [
        FIXTURE / "README.md",
        FIXTURE / "MEMORY.md",
        FIXTURE / "memory/2026-06-19.md",
    ]

    for path in required:
        assert path.exists(), path
    daily = (FIXTURE / "memory/2026-06-19.md").read_text(encoding="utf-8")
    for phrase in ["Core example", "Near drift example", "Far coherent example", "Semantic break example"]:
        assert phrase in daily
