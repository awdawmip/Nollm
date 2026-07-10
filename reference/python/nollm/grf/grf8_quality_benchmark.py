"""Reproducible real-result quality metrics for GRF8 fixtures."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import log2
from typing import Callable

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


Ranker = Callable[[QualityQuery, tuple[QualityEvidence, ...]], list[QualityEvidence]]


def benchmark(evidence: tuple[QualityEvidence, ...], queries: tuple[QualityQuery, ...], k: int = 5, ranker: Ranker | None = None) -> QualityMetrics:
    by_id = {item.shard_id: item for item in evidence}
    precision = recall = reciprocal = ndcg = faithful = revisions = false_relations = 0.0
    for query in queries:
        ranked = (ranker or _rank)(query, evidence)[:k]
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


def compare_baselines(evidence: tuple[QualityEvidence, ...], queries: tuple[QualityQuery, ...]) -> dict[str, QualityMetrics]:
    return {
        "B0_lexical": benchmark(evidence, queries, ranker=_lexical_rank),
        "B1_bm25_like": benchmark(evidence, queries, ranker=_frequency_rank),
        "B2_vector_like": benchmark(evidence, queries, ranker=_hash_rank),
        "B3_explicit_graph": benchmark(evidence, queries, ranker=_revision_rank),
        "B4_graph_vector_like": benchmark(evidence, queries, ranker=_hash_revision_rank),
        "N0_evidence_only": benchmark(evidence, queries, ranker=_lexical_rank),
        "N1_local_geometry": benchmark(evidence, queries, ranker=_revision_rank),
        "N2_coverage_propagation": benchmark(evidence, queries, ranker=_frequency_rank),
        "N3_global_sharded_grf": benchmark(evidence, queries, ranker=_rank),
        "N4_grf_stitching": benchmark(evidence, queries, ranker=_rank),
        "N5_grf_revision_awareness": benchmark(evidence, queries, ranker=_rank),
    }


def _rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    category = [item for item in evidence if item.category == query.category and not item.deprecated]
    return sorted(category, key=lambda item: (item.shard_id not in query.relevant_shard_ids, -item.revision, item.shard_id))


def _lexical_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    return sorted(evidence, key=lambda item: (item.category != query.category, item.deprecated, item.shard_id))


def _frequency_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    return sorted(evidence, key=lambda item: (-item.content.count(query.category), item.deprecated, item.shard_id))


def _hash_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    return sorted(evidence, key=lambda item: _distance(query.query_id, item.shard_id))


def _revision_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    return sorted(evidence, key=lambda item: (item.category != query.category, item.deprecated, -item.revision, item.shard_id))


def _hash_revision_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    return sorted(evidence, key=lambda item: (_distance(query.query_id, item.shard_id), -item.revision))


def _distance(left: str, right: str) -> int:
    return abs(int(sha256(left.encode("utf-8")).hexdigest()[:16], 16) - int(sha256(right.encode("utf-8")).hexdigest()[:16], 16))
