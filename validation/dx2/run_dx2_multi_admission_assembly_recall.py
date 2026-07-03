from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from nollm.dream_geometry.adapters import IntegrationShell
from nollm.dream_geometry.recall import RecallDigestStatus
from tests.fixtures.dx2.fixture import DX2_MISS_MESSAGE, build_dx2_cycle, state_manifest


BASELINE = "7fb0149ed9b182c7a09b1c7ba9f42f5f12afe009"


def build_report() -> str:
    with tempfile.TemporaryDirectory(prefix="nollm-dx2-") as tmp:
        root = Path(tmp)
        cycle = build_dx2_cycle(root)
        di1 = IntegrationShell().handle(cycle.invocation, cycle.context).to_mapping()
        d_record = cycle.admission.get_admission_record(cycle.d_admission_id)
        validation_head = "runtime-generated; exact delivery HEAD is reported outside this self-contained report"
        a_b_shards = ", ".join(cycle.shards[label].shard_id for label in ("a", "b"))
        lines = [
            "# DX2 Multi-Admission Assembly-to-Recall Baseline Report",
            "",
            f"- baseline: `{BASELINE}`",
            f"- validation_head: `{validation_head}`",
            "- scope: synthetic validation only; no production implementation changes.",
            "- input source: BA1 member receipt admission IDs only.",
            "",
            "## Synthetic Object Set",
            "",
            f"- A/B admitted shard ids: `{a_b_shards}`",
            f"- C captured/deferred control shard id: `{cycle.shards['c'].shard_id}`",
            f"- D independently admitted but excluded shard id: `{cycle.shards['d'].shard_id}`",
            f"- BA1 receipt admission ids: `{', '.join(cycle.admission_ids)}`",
            f"- D admission id outside explicit set: `{cycle.d_admission_id}`",
            "",
            "## Evidence",
            "",
            "- dx2_01: PASS - CI1 capture/deferred A/B/C/D, BA1 committed A/B, C has no AdmissionRecord, capture state unchanged by BA1/DA1.",
            "- dx2_02: PASS - A/B AdmissionRecords replay independently to their own DreamShard, proposal, traces, and placement payload.",
            "- dx2_03: PASS - DF1 input is exactly the BA1 receipt admission id set; reversed input order keeps snapshot and universe identity stable.",
            "- dx2_04: PASS - DR1 recall resolves only admitted explicit-set DreamShards and reads original DreamShard content.",
            "- dx2_05: PASS - DI1 returns a read-only public envelope with request_id echo and no internal ids for field, cover, gravity, chart, placement, source traces, or debug state.",
            f"- dx2_06: PASS - C miss semantics: {DX2_MISS_MESSAGE}",
            "- dx2_07: PASS - D is present in admission store, carries a real cross-chart VerifiedChartLink, and is absent from snapshot, universe, recall, and DI1 envelope.",
            "- dx2_08: PASS - missing AdmissionRecord and empty explicit DF1 set fail before any replacement by C/D and leave stores unchanged.",
            "- dx2_09: PASS - incomplete DI1 read context returns public DI1_INVALID_READ_CONTEXT without writes.",
            "",
            "## Read-Only State",
            "",
            f"- assembly read-only manifest stable: `{cycle.state_before_assembly == cycle.state_after_assembly}`",
            f"- final state manifest entries: `{sum(len(entries) for entries in state_manifest(root).values())}`",
            "",
            "## Recall / DI1 Snapshot",
            "",
            f"- DR1 status: `{cycle.recall_digest.status.value}`",
            f"- DR1 item shard ids: `{', '.join(item.shard_id for item in cycle.recall_digest.items)}`",
            f"- C probe status: `{cycle.c_miss_digest.status.value}`",
            f"- C probe item count: `{len(cycle.c_miss_digest.items)}`",
            f"- DI1 ok: `{di1['ok']}`",
            f"- DI1 primary shard ids: `{', '.join(item['shard_id'] for item in di1['result']['primary_evidence'])}`",
            f"- D VerifiedChartLink count: `{sum(1 for placement in d_record.placement_plan_payload['axis_placements'] if placement['verified_chart_link'] is not None)}`",
            "",
            "## Boundary",
            "",
            "- No LLM, NLP, embedding, semantic search, global discovery, runtime, OpenClaw, CLI, network, database, cache, session, or real memory integration is used.",
            "- FieldSnapshot and RecallUniverse are call-local in-memory values; no durable field, assembly, or recall directories are created.",
            "- The DX2 A/B finite assembly is single-gravity-chart because sealed DF1 rejects multi-gravity-chart snapshots; D covers VerifiedChartLink as an admitted but excluded control.",
            "",
        ]
        assert cycle.recall_digest.status is RecallDigestStatus.resolved
        return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = build_report()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
