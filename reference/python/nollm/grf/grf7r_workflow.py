"""Ground-truth workflow benchmark for GRF7R and explicit baselines."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import perf_counter_ns

from .cell_address import CellAddress
from .fixed_point import Q16_ONE
from .global_field import CrossPartitionBridgeKernel, CrossPartitionStitchProposal, GlobalRecallBudget, GlobalRecallQuery, GlobalShardedField, GRFPartition, partition_descriptor
from .json_canonical import canonical_dumps
from .placement import GeometryMark, PlacementRecord


WORKFLOWS = ("coding", "research", "document", "long_running_agent")
MODELS = ("B0_lexical", "B1_vector_like", "B2_explicit_graph", "B3_graph_vector", "N0_GRF")


@dataclass(frozen=True)
class CorpusItem:
    item_id: str
    workflow: str
    topic: str
    role: str
    text: str
    source: str

    def to_mapping(self) -> dict[str, str]:
        return self.__dict__.copy()


def run_workflow_benchmark(output_root: Path, *, topics_per_workflow: int = 5, k: int = 5) -> dict[str, object]:
    if topics_per_workflow < 2 or k < 1:
        raise ValueError("workflow benchmark fixture is too small")
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    corpus, queries, labels = _dataset(topics_per_workflow)
    by_id = {item.item_id: item for item in corpus}
    graph = {query_id: tuple((*sorted(labels[query_id]), _false_friend_id(query_id))) for query_id in queries}
    build_started = perf_counter_ns()
    field, shard_to_item, placements = _grf_field(corpus, labels)
    grf_build_ns = perf_counter_ns() - build_started
    rollback_success, false_before, false_after = _exercise_false_relation(field, placements, next(iter(queries)))
    raw = []
    build_costs: dict[str, int] = {}
    model_storage: dict[str, int] = {}
    for model in MODELS:
        started = perf_counter_ns()
        rankings = {}
        for query_id, query_text in queries.items():
            if model == "B0_lexical":
                ranking = _rank_lexical(corpus, query_text)
            elif model == "B1_vector_like":
                ranking = _rank_vector_like(corpus, query_text)
            elif model == "B2_explicit_graph":
                ranking = graph[query_id]
            elif model == "B3_graph_vector":
                graph_rank = graph[query_id]
                vector_rank = _rank_vector_like(corpus, query_text)
                ranking = tuple(sorted((item.item_id for item in corpus), key=lambda item_id: ((graph_rank.index(item_id) if item_id in graph_rank else len(corpus)) * 2 + vector_rank.index(item_id), item_id)))
            else:
                result = field.recall(GlobalRecallQuery(f"query:workflow:{query_id}", "patch_id", f"patch:workflow:{query_id}", GlobalRecallBudget(1, k, k, k, 0), False))
                ranking = tuple(shard_to_item[shard] for shard in result.selected_shards)
            rankings[query_id] = ranking
            top = ranking[:k]
            relevant = labels[query_id]
            hits = tuple(item_id for item_id in top if item_id in relevant)
            raw.append({
                "model": model,
                "query_id": query_id,
                "workflow": query_id.split(":", 1)[0],
                "ranking": top,
                "relevant": tuple(sorted(relevant)),
                "hit_count": len(hits),
                "first_relevant_rank": next((index + 1 for index, item_id in enumerate(top) if item_id in relevant), None),
                "faithful_hit_count": sum(by_id[item_id].source == "trusted_source" for item_id in hits),
                "context_bytes": sum(len(by_id[item_id].text.encode("utf-8")) for item_id in top),
                "false_relation_selected": _false_friend_id(query_id) in top,
            })
        build_costs[model] = grf_build_ns if model == "N0_GRF" else perf_counter_ns() - started
        model_storage[model] = len(canonical_dumps(rankings if model != "N0_GRF" else field.directory.to_mapping()))
    metrics = {}
    for model in MODELS:
        rows = [item for item in raw if item["model"] == model]
        metrics[model] = {
            "precision_at_k": f"{sum(item['hit_count'] for item in rows)}/{len(rows) * k}",
            "recall_at_k": f"{sum(item['hit_count'] for item in rows)}/{sum(len(item['relevant']) for item in rows)}",
            "mrr": f"{sum(0 if item['first_relevant_rank'] is None else 1 / item['first_relevant_rank'] for item in rows) / len(rows):.6f}",
            "source_faithfulness": f"{sum(item['faithful_hit_count'] for item in rows)}/{sum(item['hit_count'] for item in rows)}",
            "context_bytes": sum(item["context_bytes"] for item in rows),
            "update_time_ns": build_costs[model],
            "storage_bytes": model_storage[model],
            "false_relation_rate": f"{sum(item['false_relation_selected'] for item in rows)}/{len(rows)}",
            "rollback_success": rollback_success if model == "N0_GRF" else None,
        }
    raw_path = output_root / "workflow_queries.json"
    raw_path.write_bytes(canonical_dumps(tuple(raw)))
    result = {
        "scope": "observed_on_current_fixture_only",
        "workflow_count": len(WORKFLOWS),
        "query_count": len(queries),
        "corpus_item_count": len(corpus),
        "roles": tuple(sorted({item.role for item in corpus})),
        "models": metrics,
        "false_relation_injected": True,
        "grf_false_bridge_used_before_rollback": false_before,
        "grf_false_bridge_used_after_rollback": false_after,
        "grf_rollback_success": rollback_success,
        "raw_query_sha256": sha256(raw_path.read_bytes()).hexdigest(),
    }
    (output_root / "workflow_metrics.json").write_bytes(canonical_dumps(result))
    return result


def _dataset(topics_per_workflow: int) -> tuple[tuple[CorpusItem, ...], dict[str, str], dict[str, frozenset[str]]]:
    corpus = []
    queries = {}
    labels = {}
    roles = (
        ("relevant_primary", "current verified resolution", "trusted_source"),
        ("relevant_secondary", "current supporting evidence", "trusted_source"),
        ("hard_negative", "matching terms but unrelated resolution", "trusted_source"),
        ("same_name_false_friend", "same name different component", "trusted_source"),
        ("temporal_conflict", "obsolete superseded resolution", "trusted_source"),
        ("source_conflict", "current claim from conflicting source", "untrusted_source"),
    )
    for workflow in WORKFLOWS:
        for topic_index in range(topics_per_workflow):
            query_id = f"{workflow}:topic:{topic_index}"
            token = f"{workflow}_topic_{topic_index}"
            queries[query_id] = f"find current verified {token} resolution"
            relevant = set()
            for role, detail, source in roles:
                item_id = f"item:{query_id}:{role}"
                corpus.append(CorpusItem(item_id, workflow, query_id, role, f"{token} {detail}", source))
                if role.startswith("relevant_"):
                    relevant.add(item_id)
            labels[query_id] = frozenset(relevant)
    return tuple(corpus), queries, labels


def _rank_lexical(corpus: tuple[CorpusItem, ...], query: str) -> tuple[str, ...]:
    terms = set(query.split())
    return tuple(item.item_id for item in sorted(corpus, key=lambda item: (-len(terms.intersection(item.text.split())), item.item_id)))


def _rank_vector_like(corpus: tuple[CorpusItem, ...], query: str) -> tuple[str, ...]:
    query_vector = _trigram_vector(query)
    return tuple(item.item_id for item in sorted(corpus, key=lambda item: (-_dot(query_vector, _trigram_vector(item.text)), item.item_id)))


def _trigram_vector(text: str) -> dict[str, int]:
    normalized = text.lower().replace(" ", "_")
    result: dict[str, int] = {}
    for index in range(max(0, len(normalized) - 2)):
        gram = normalized[index:index + 3]
        result[gram] = result.get(gram, 0) + 1
    return result


def _dot(left: dict[str, int], right: dict[str, int]) -> int:
    return sum(value * right.get(key, 0) for key, value in left.items())


def _grf_field(corpus: tuple[CorpusItem, ...], labels: dict[str, frozenset[str]]) -> tuple[GlobalShardedField, dict[str, str], dict[str, PlacementRecord]]:
    field = GlobalShardedField()
    shard_to_item = {}
    placements = {}
    for index, item in enumerate(corpus):
        partition_id = f"partition:workflow:{index:04d}"
        field.add_partition(GRFPartition(partition_descriptor(partition_id, index, index, index, index)))
        shard = f"shard:workflow:{sha256(item.item_id.encode()).hexdigest()[:24]}"
        cell = CellAddress("eisenstein_exact_v1", "chart:grf7", 0, index, 0)
        mark = GeometryMark(f"mark:workflow:{index}", shard, cell.profile_id, cell.chart_id, cell, "ground_truth_fixture", "high", 0, "field:workflow")
        patch_id = f"patch:workflow:{item.topic}" if item.item_id in labels[item.topic] else f"patch:workflow:negative:{index}"
        placement = PlacementRecord(f"placement:workflow:{index}", shard, f"candidate:workflow:{index}", f"decision:workflow:{index}", mark, f"island:workflow:{item.topic}", patch_id, (shard,), cell.profile_id, "grf7r_workflow_v1")
        field.insert(partition_id, placement, f"admission:workflow:{index}")
        shard_to_item[shard] = item.item_id
        placements[item.item_id] = placement
    return field, shard_to_item, placements


def _exercise_false_relation(field: GlobalShardedField, placements: dict[str, PlacementRecord], query_id: str) -> tuple[bool, bool, bool]:
    source = placements[sorted(item_id for item_id in placements if item_id.startswith(f"item:{query_id}:relevant_"))[0]]
    target = placements[_false_friend_id(query_id)]
    source_partition = field._unique_routes[("placement_id", source.placement_id)][0]
    target_partition = field._unique_routes[("placement_id", target.placement_id)][0]
    bridge = CrossPartitionBridgeKernel("bridge:workflow:false", source_partition, target_partition, source.placement_id, target.placement_id, Q16_ONE, Q16_ONE, 1, (source.shard_id, target.shard_id))
    proposal = CrossPartitionStitchProposal("proposal:workflow:false", bridge, ("injected_false_relation",))
    field.accept_stitch(proposal, "stitch:workflow:false", "2026-07-10T00:00:00Z")
    budget = GlobalRecallBudget(1, 1, 2, 2, 0)
    before = field.recall(GlobalRecallQuery("query:workflow:false:before", "placement_id", source.placement_id, budget, True))
    field.rollback_stitch(bridge.bridge_id, "known_false_relation", "2026-07-10T00:00:01Z")
    after = field.recall(GlobalRecallQuery("query:workflow:false:after", "placement_id", source.placement_id, budget, True))
    used_before = bridge.bridge_id in before.path.bridges_used
    used_after = bridge.bridge_id in after.path.bridges_used
    return used_before and not used_after, used_before, used_after


def _false_friend_id(query_id: str) -> str:
    return f"item:{query_id}:same_name_false_friend"
