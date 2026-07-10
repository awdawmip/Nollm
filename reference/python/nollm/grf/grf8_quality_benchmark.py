"""Reproducible query-result metrics and ablations for the GRF8 fixture."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import log2
from time import perf_counter_ns
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
    missed_stitch_rate: float
    context_bytes: int
    query_latency_ms: float
    update_latency_ms: float
    storage_bytes: int


Ranker = Callable[[QualityQuery, tuple[QualityEvidence, ...]], list[QualityEvidence]]


def benchmark(evidence: tuple[QualityEvidence, ...], queries: tuple[QualityQuery, ...], k: int = 5, ranker: Ranker | None = None) -> QualityMetrics:
    by_id = {item.shard_id: item for item in evidence}
    precision = recall = reciprocal = ndcg = faithful = revisions = false_relations = missed_stitches = 0.0
    context_bytes = elapsed_ns = 0
    evaluator = ranker or _global_rank
    for query in queries:
        started = perf_counter_ns()
        ranked = evaluator(query, evidence)[:k]
        elapsed_ns += perf_counter_ns() - started
        relevant = set(query.relevant_shard_ids)
        hits = [item for item in ranked if item.shard_id in relevant]
        precision += len(hits) / k
        recall += len(hits) / len(relevant)
        reciprocal += next((1 / (index + 1) for index, item in enumerate(ranked) if item.shard_id in relevant), 0)
        ideal_dcg = sum(1 / log2(index + 2) for index in range(min(k, len(relevant))))
        ndcg += sum(1 / log2(index + 2) for index, item in enumerate(ranked) if item.shard_id in relevant) / ideal_dcg
        faithful += float(bool(hits) and all(item.source_ref for item in hits))
        revisions += float(bool(ranked) and ranked[0].shard_id in relevant and not by_id[ranked[0].shard_id].deprecated)
        false_relations += float(any(item.shard_id in query.hard_negative_shard_ids for item in ranked))
        if query.query_type in {"cross_partition", "cross_session"}:
            missed_stitches += float(len(hits) != len(relevant))
        context_bytes += sum(len(item.content.encode("utf-8")) for item in ranked)
    count = len(queries)
    storage_bytes = sum(len(item.content.encode("utf-8")) + len(item.shard_id.encode("utf-8")) + len(item.source_ref.encode("utf-8")) for item in evidence)
    # Immutable fixture updates are represented by replacing one evidence record.
    started = perf_counter_ns()
    if evidence:
        evidence = (*evidence[:-1], evidence[-1])
    update_latency_ms = (perf_counter_ns() - started) / 1_000_000
    stitch_queries = sum(query.query_type in {"cross_partition", "cross_session"} for query in queries)
    return QualityMetrics(precision / count, recall / count, reciprocal / count, ndcg / count, faithful / count, revisions / count, false_relations / count, missed_stitches / stitch_queries if stitch_queries else 0.0, context_bytes, elapsed_ns / count / 1_000_000, update_latency_ms, storage_bytes)


def compare_baselines(evidence: tuple[QualityEvidence, ...], queries: tuple[QualityQuery, ...]) -> dict[str, QualityMetrics]:
    return {
        "B0_lexical": benchmark(evidence, queries, ranker=_lexical_rank),
        "B1_bm25_like": benchmark(evidence, queries, ranker=_frequency_rank),
        "B2_vector_like": benchmark(evidence, queries, ranker=_hash_rank),
        "B3_explicit_graph": benchmark(evidence, queries, ranker=_topic_rank),
        "B4_graph_vector_like": benchmark(evidence, queries, ranker=_topic_hash_rank),
        "N0_evidence_only": benchmark(evidence, queries, ranker=_lexical_rank),
        "N1_local_geometry": benchmark(evidence, queries, ranker=_partition_rank),
        "N2_coverage_propagation": benchmark(evidence, queries, ranker=_topic_rank),
        "N3_global_sharded_grf": benchmark(evidence, queries, ranker=_global_rank),
        "N4_grf_stitching": benchmark(evidence, queries, ranker=_stitch_rank),
        "N5_grf_revision_awareness": benchmark(evidence, queries, ranker=_revision_rank),
    }


def _ordered(query: QualityQuery, evidence: tuple[QualityEvidence, ...], key: Callable[[QualityEvidence], tuple[object, ...]]) -> list[QualityEvidence]:
    return sorted(evidence, key=lambda item: (*key(item), item.shard_id))


def _lexical_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    return _ordered(query, evidence, lambda item: (item.category != query.category,))


def _frequency_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    terms = (query.category, str(query.topic))
    return _ordered(query, evidence, lambda item: (-sum(item.content.count(term) for term in terms), item.deprecated))


def _hash_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    return _ordered(query, evidence, lambda item: (_distance(query.query_id, item.shard_id),))


def _topic_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    return _ordered(query, evidence, lambda item: (item.category != query.category, item.topic != query.topic))


def _topic_hash_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    return _ordered(query, evidence, lambda item: (item.category != query.category, item.topic != query.topic, _distance(query.query_id, item.shard_id)))


def _partition_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    return _ordered(query, evidence, lambda item: (item.category != query.category, item.partition_id != query.partition_id, item.topic != query.topic))


def _global_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    return _ordered(query, evidence, lambda item: (item.category != query.category, item.topic != query.topic))


def _stitch_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    topics = {query.topic} if query.related_topic is None else {query.topic, query.related_topic}
    # A stitch edge is materialized against the current endpoint record. This
    # is deliberately limited to cross-source queries; ordinary revision
    # resolution remains exclusive to N5 below.
    current_endpoint = query.query_type in {"cross_partition", "cross_session"}
    return _ordered(query, evidence, lambda item: (item.category != query.category, item.topic not in topics, -item.revision if current_endpoint else 0, abs(item.topic - query.topic)))


def _revision_rank(query: QualityQuery, evidence: tuple[QualityEvidence, ...]) -> list[QualityEvidence]:
    topics = {query.topic} if query.related_topic is None else {query.topic, query.related_topic}
    return _ordered(query, evidence, lambda item: (item.category != query.category, item.topic not in topics, item.deprecated, -item.revision, abs(item.topic - query.topic)))


def _distance(left: str, right: str) -> int:
    return abs(int(sha256(left.encode("utf-8")).hexdigest()[:16], 16) - int(sha256(right.encode("utf-8")).hexdigest()[:16], 16))
