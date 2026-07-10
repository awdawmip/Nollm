"""Deterministic, auditable quality fixture for GRF8 query evaluation."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


CATEGORIES = ("project", "coding", "research", "document", "conversation", "decision_revision")
_REVISIONS = 3


@dataclass(frozen=True)
class QualityEvidence:
    shard_id: str
    category: str
    content: str
    revision: int
    deprecated: bool
    source_ref: str
    topic: int = 0
    partition_id: str = "partition:0"
    session_id: str = "session:0"


@dataclass(frozen=True)
class QualityQuery:
    query_id: str
    category: str
    query_type: str
    relevant_shard_ids: tuple[str, ...]
    hard_negative_shard_ids: tuple[str, ...]
    topic: int = 0
    related_topic: int | None = None
    partition_id: str = "partition:0"
    session_id: str = "session:0"


def build_quality_dataset(evidence_count: int = 10_000, query_count: int = 1_000, seed: int = 7008010) -> tuple[tuple[QualityEvidence, ...], tuple[QualityQuery, ...]]:
    if evidence_count < len(CATEGORIES) * _REVISIONS or query_count < len(CATEGORIES):
        raise ValueError("GRF8 dataset requires all categories and revision chains")
    evidence: list[QualityEvidence] = []
    for index in range(evidence_count):
        category = CATEGORIES[index % len(CATEGORIES)]
        chain_index = index // len(CATEGORIES)
        topic, revision = divmod(chain_index, _REVISIONS)
        partition_id = f"partition:{topic % 17}"
        session_id = f"session:{topic % 13}"
        evidence.append(QualityEvidence(
            f"shard:grf8:{category}:{topic}:{revision}", category,
            f"{category} topic {topic} revision {revision} source fact",
            revision, revision < _REVISIONS - 1, f"source:grf8:{category}:{topic}",
            topic, partition_id, session_id,
        ))
    by_key = {(item.category, item.topic, item.revision): item for item in evidence}
    # Queries draw only from fully populated category/revision chains. Any
    # remaining rows still model an uneven corpus, but are never ground truth.
    topic_count = evidence_count // (len(CATEGORIES) * _REVISIONS)
    queries: list[QualityQuery] = []
    query_types = ("direct_fact", "latest_valid_revision", "cross_partition", "cross_session")
    for index in range(query_count):
        category = CATEGORIES[index % len(CATEGORIES)]
        topic = (seed + index * 17) % topic_count
        related_topic = (topic + 1) % topic_count
        query_type = query_types[index % len(query_types)]
        primary = by_key[(category, topic, _REVISIONS - 1)]
        related = by_key[(category, related_topic, _REVISIONS - 1)]
        relevant = (primary,) if query_type in {"direct_fact", "latest_valid_revision"} else (primary, related)
        negative = by_key[(category, (topic + 2) % topic_count, _REVISIONS - 1)]
        queries.append(QualityQuery(
            f"query:grf8:{index}", category, query_type,
            tuple(item.shard_id for item in relevant), (negative.shard_id,), topic,
            related_topic if len(relevant) == 2 else None, primary.partition_id, primary.session_id,
        ))
    return tuple(evidence), tuple(queries)


def dataset_digest(evidence: tuple[QualityEvidence, ...], queries: tuple[QualityQuery, ...]) -> str:
    return sha256(repr((evidence, queries)).encode("utf-8")).hexdigest()
