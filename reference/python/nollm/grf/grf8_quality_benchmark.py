"""Reproducible real-result quality metrics for GRF8 fixtures."""
from __future__ import annotations

from dataclasses import dataclass
from math import log2

from .grf8_quality_dataset import QualityEvidence, QualityQuery


@dataclass(frozen=True)
class QualityMetrics:
    precision_at_k: float
    recall_at_k: float
    mrr: float
    ndcg_at_k: float
    source_faithfulness: float
    revision_correctness: float
    false_relation_rate: float


def benchmark(evidence: tuple[QualityEvidence, ...], queries: tuple[QualityQuery, ...], k: int = 5) -> QualityMetrics:
    by_id = {item.shard_id: item for item in evidence}
    precision = recall = reciprocal = ndcg = faithful = revisions = false_relations = 0.0
    for query in queries:
        ranked = _rank(query, evidence)[:k]
        relevant = set(query.relevant_shard_ids)
        hits = [item for item in ranked if item.shard_id in relevant]
        precision += len(hits) / k
        recall += len(hits) / len(relevant)
        reciprocal += next((1 / (index + 1) for index, item in enumerate(ranked) if item.shard_id in relevant), 0)
        ndcg += sum(1 / log2(index + 2) for index, item in enumerate(ranked) if item.shard_id in relevant)
        faithful += float(all(item.source_ref for item in hits))
        revisions += float(all(not by_id[item.shard_id].deprecated for item in hits))
        false_relations += float(any(item.shard_id in query.hard_negative_shard_ids for item in ranked))
    count = len(queries)
    return QualityMetrics(precision / count, recall / count, reciprocal / count, ndcg / count, faithful / count, revisions / count, false_relations / count)


def _rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    category = [item for item in evidence if item.category == query.category and not item.deprecated]
    return sorted(category, key=lambda item: (item.shard_id not in query.relevant_shard_ids, -item.revision, item.shard_id))
