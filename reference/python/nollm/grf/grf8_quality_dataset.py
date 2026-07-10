"""Deterministic GRF8 memory-quality fixture with auditable ground truth."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


CATEGORIES = ("project", "coding", "research", "document", "conversation", "decision_revision")


@dataclass(frozen=True)
class QualityEvidence:
    shard_id: str
    category: str
    content: str
    revision: int
    deprecated: bool
    source_ref: str


@dataclass(frozen=True)
class QualityQuery:
    query_id: str
    category: str
    query_type: str
    relevant_shard_ids: tuple[str, ...]
    hard_negative_shard_ids: tuple[str, ...]


def build_quality_dataset(evidence_count: int = 10_000, query_count: int = 1_000, seed: int = 7008010) -> tuple[tuple[QualityEvidence, ...], tuple[QualityQuery, ...]]:
    if evidence_count < 6 or query_count < 6:
        raise ValueError("GRF8 dataset requires all categories")
    evidence = []
    for index in range(evidence_count):
        category = CATEGORIES[index % len(CATEGORIES)]
        topic = index // len(CATEGORIES)
        revision = topic % 3
        deprecated = revision == 0 and topic % 5 == 0
        shard_id = f"shard:grf8:{category}:{topic}:{revision}"
        evidence.append(QualityEvidence(shard_id, category, f"{category} topic {topic} revision {revision} source fact", revision, deprecated, f"source:grf8:{category}:{topic}"))
    queries = []
    for index in range(query_count):
        category = CATEGORIES[index % len(CATEGORIES)]
        candidates = [item for item in evidence if item.category == category]
        target = candidates[(seed + index * 17) % len(candidates)]
        negative = candidates[((seed + index * 17) + 1) % len(candidates)]
        if negative.shard_id == target.shard_id:
            negative = candidates[(candidates.index(negative) + 1) % len(candidates)]
        queries.append(QualityQuery(f"query:grf8:{index}", category, ("latest_valid_revision" if index % 3 == 0 else "direct_fact"), (target.shard_id,), (negative.shard_id,)))
    return tuple(evidence), tuple(queries)


def dataset_digest(evidence: tuple[QualityEvidence, ...], queries: tuple[QualityQuery, ...]) -> str:
    return sha256(repr((evidence, queries)).encode("utf-8")).hexdigest()
