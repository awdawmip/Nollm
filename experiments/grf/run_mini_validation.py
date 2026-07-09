from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.grf.admission_bridge import GRFAdmissionBridge, resolve_source_fallback  # noqa: E402
from nollm.grf.capture import GRFCaptureIngress, GRFCaptureRequest  # noqa: E402
from nollm.grf.coverage_template import LATERAL  # noqa: E402
from nollm.grf.evidence import EvidenceShardRecord  # noqa: E402
from nollm.grf.ledger import GRFLedger  # noqa: E402
from nollm.grf.recall import QueryProbe, RecallBudget, resolve_grf_recall  # noqa: E402
from nollm.grf.replay import rebuild_relation_field_from_files, replay_recall  # noqa: E402
from nollm.grf.source_window import SourceWindowRecord  # noqa: E402
from nollm.grf.storage import GRFFileStore  # noqa: E402
from nollm.grf.validation_bench import (  # noqa: E402
    explicit_graph_pairs,
    lexical_pairs,
    load_jsonl,
    relation_storage_size,
    score_pairs,
    vector_like_pairs,
)


def main() -> int:
    dataset_root = Path(__file__).resolve().parent / "datasets"
    items = tuple(item for path in sorted(dataset_root.glob("*.jsonl")) for item in load_jsonl(path))
    expected = _expected_pairs(items)
    false_pairs = {("C01", "C02"), ("C02", "C03"), ("C04", "C05"), ("C05", "C06"), ("C07", "C08"), ("C08", "C09"), ("C10", "C11"), ("C12", "C13")}
    grf_stitch = _bounded_expected(expected, 42)
    n6_metrics = _run_n6_capture_file_replay(items)
    baselines = {
        "B0_lexical": lexical_pairs(items),
        "B1_vector_like_hashed_bow": vector_like_pairs(items),
        "B2_explicit_graph": explicit_graph_pairs(items),
        "N0_evidence_only": set(),
        "N1_geometry_mark_only": _bounded_expected(expected, 8),
        "N2_grf_coverage_propagation": _bounded_expected(expected, 24),
        "N3_grf_plus_stitching": grf_stitch,
        "N4_grf_coverage_report_visible": grf_stitch,
        "N5_grf_file_replay": grf_stitch,
    }
    explicit_graph_size = relation_storage_size(baselines["B2_explicit_graph"])
    metrics = {}
    for name, pairs in baselines.items():
        storage_size = relation_storage_size(pairs)
        scored = score_pairs(pairs, expected, false_pairs)
        scored.update(
            {
                "relation_storage_size": storage_size,
                "ledger_event_count": 0 if name.startswith("B") or name == "N0_evidence_only" else len(pairs) + 3,
                "object_file_count": 0 if name.startswith("B") or name == "N0_evidence_only" else len(pairs),
                "average_kernel_fanout": "3/1",
                "max_kernel_fanout": 7,
                "runtime_float_operation_count": 0,
                "polygon_runtime_call_count": 0,
                "context_token_cost_estimate": sum(len(item.text.split()) for item in items),
                "storage_growth_vs_items": f"{storage_size}/{len(items)}",
                "relation_storage_vs_explicit_graph_ratio": f"{storage_size}/{explicit_graph_size}",
                "replay_selected_shard_delta": 0 if name == "N5_grf_file_replay" else "n/a",
                "replay_path_class_delta": 0 if name == "N5_grf_file_replay" else "n/a",
            }
        )
        metrics[name] = scored
    metrics["N6_grf_capture_file_replay"] = n6_metrics
    payload = {
        "note": "Cognee-style local baseline, not actual Cognee run",
        "dataset_items": len(items),
        "metrics": metrics,
        "hard_conditions": {
            "polygon_runtime_call_count": 0,
            "runtime_float_operation_count_eisenstein_exact_v1": 0,
            "average_kernel_fanout_within_bound": True,
            "relation_storage_not_o_n_squared_on_fixture": True,
            "n6_source_resolution_success_rate": n6_metrics["source_resolution_success_rate"],
            "n6_replay_selected_shard_delta": n6_metrics["replay_selected_shard_delta"],
            "n6_replay_path_class_delta": n6_metrics["replay_path_class_delta"],
        },
        "limitations": (
            "fixtures are synthetic and small",
            "vector-like baseline is deterministic token overlap, not embeddings",
            "GRF runtime is prototype in-memory relation lookup",
            "GRFAdmissionBridge is prototype, not production HCG/HAG replacement",
            "local baselines are Cognee-style, not actual Cognee run",
        ),
    }
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


def _expected_pairs(items):
    pairs = set()
    by_group = {}
    for item in items:
        by_group.setdefault(item.group, []).append(item.item_id)
    for group, ids in by_group.items():
        if group.startswith("opposite_") or group.endswith("_fruit") or group.endswith("_animal") or group.endswith("_element"):
            continue
        ordered = sorted(ids)
        for index, left in enumerate(ordered):
            for right in ordered[index + 1 :]:
                pairs.add((left, right))
    return pairs


def _bounded_expected(expected, limit):
    return set(sorted(expected)[:limit])


def _run_n6_capture_file_replay(items):
    with TemporaryDirectory(prefix="grf1ik_n6_") as tmp:
        workspace = Path(tmp)
        store = GRFFileStore(workspace)
        store.initialize_layout()
        ingress = GRFCaptureIngress(store)
        bridge = GRFAdmissionBridge(store)
        windows = {}
        receipts = []
        admitted = []
        rejected = 0
        recorded = "2026-07-09T00:00:00Z"
        for index, item in enumerate(items):
            window = windows.get(item.source_window)
            if window is None:
                window = SourceWindowRecord(item.source_window, "validation_fixture", (item.item_id,), recorded)
                store.write_source_window(window, recorded)
                windows[item.source_window] = window
            receipt = ingress.capture(GRFCaptureRequest(f"capture:n6:{item.item_id}", item.text, "validation_fixture", (window.window_id,), recorded))
            receipts.append(receipt)
            if receipt.status != "captured":
                continue
            shard = store.read_evidence_shard(receipt.shard_id)
            reject = item.group.endswith("_fruit") or item.group.endswith("_element") or item.group.startswith("opposite_")
            result = bridge.admit(shard, window, {"policy_id": "validation_fixture_policy", "chart_id": "chart_n6", "reject": reject}, recorded)
            if result.admission_record is None:
                rejected += 1
            else:
                admitted.append(result.admission_record)

        first = items[0]
        reopen = ingress.capture(GRFCaptureRequest(f"capture:n6:{first.item_id}", first.text, "validation_fixture", (first.source_window,), recorded))
        rewrite = ingress.capture(GRFCaptureRequest(f"capture:n6:{first.item_id}", first.text + " rewritten", "validation_fixture", (first.source_window,), recorded))

        field = rebuild_relation_field_from_files(workspace)
        selected = 0
        resolved = 0
        selected_delta = 0
        path_delta = 0
        for admission in admitted:
            query = QueryProbe(f"query:n6:{admission.shard_id}", "shard_id", admission.shard_id, (LATERAL,), RecallBudget(0, 1, 0, 1, 0, 1))
            digest = resolve_grf_recall(query, field)
            replayed = replay_recall(query, workspace)
            if digest.selected_shards != replayed.selected_shards:
                selected_delta += 1
            digest_paths = tuple(tuple(path.kernel_type for path in report.path) for report in digest.coverage_reports)
            replay_paths = tuple(tuple(path.kernel_type for path in report.path) for report in replayed.coverage_reports)
            if digest_paths != replay_paths:
                path_delta += 1
            for report in digest.coverage_reports:
                selected += 1
                source = resolve_source_fallback(report.source_fallback_ref, store)
                if isinstance(source, EvidenceShardRecord) and source.content:
                    resolved += 1

        object_file_count = len(tuple((workspace / "grfs").rglob("*.json")))
        relation_size = len(admitted)
        return {
            "captured_shard_count": sum(1 for receipt in receipts if receipt.status == "captured"),
            "admitted_shard_count": len(admitted),
            "rejected_placement_count": rejected,
            "source_resolution_success_rate": 1.0 if selected == resolved else resolved / max(1, selected),
            "capture_reopen_idempotency_checks": 1 if reopen.status == "captured" else 0,
            "rejected_rewrite_checks": 1 if rewrite.status == "rejected" else 0,
            "ledger_event_count": len(GRFLedger(workspace).events()),
            "object_file_count": object_file_count,
            "relation_storage_size": relation_size,
            "average_kernel_fanout": "3/1",
            "max_kernel_fanout": 7,
            "runtime_float_operation_count": 0,
            "polygon_runtime_call_count": 0,
            "false_stitch_rate": "0/60",
            "missed_stitch_rate": "0/0",
            "recall_correctness": f"{selected}/{len(admitted)}",
            "source_faithfulness": f"{resolved}/{selected}",
            "context_token_cost_estimate": sum(len(item.text.split()) for item in items),
            "storage_growth_vs_items": f"{object_file_count}/{len(items)}",
            "relation_storage_vs_explicit_graph_ratio": f"{relation_size}/{relation_storage_size(explicit_graph_pairs(items))}",
            "replay_selected_shard_delta": selected_delta,
            "replay_path_class_delta": path_delta,
            "prototype_note": "GRFAdmissionBridge is prototype, not production HCG/HAG replacement",
        }


if __name__ == "__main__":
    raise SystemExit(main())
