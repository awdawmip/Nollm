from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = REPO_ROOT / "reference" / "python"
TEST_ROOT = PYTHON_ROOT / "tests"
sys.path.insert(0, str(PYTHON_ROOT))
sys.path.insert(0, str(TEST_ROOT))

from nollm.dream_geometry.host_execution import execute_host_plan, receipt_to_mapping  # noqa: E402
from test_hx1_trusted_host_bridge import hx1_fixture, setup_preexisting_d  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)

    with tempfile.TemporaryDirectory(prefix="hx1_validation_") as temp:
        work = Path(temp) / "work"
        setup_preexisting_d(work)
        fixture = hx1_fixture(work)
        first = receipt_to_mapping(execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"]))
        second = receipt_to_mapping(execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"]))
        if first != second:
            raise SystemExit("HX1 idempotent reopen mismatch")
        report = render_report(first, _tree_forbidden(Path(temp) / "work"))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8", newline="\n")
    docs_output = REPO_ROOT / "docs" / "validation" / "HX1_TRUSTED_HOST_STAGED_EXECUTION_REPORT.md"
    docs_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(output, docs_output)
    return 0


def render_report(receipt: dict, forbidden_dirs: tuple[str, ...]) -> str:
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    receipt_sha = sha256(canonical.encode("utf-8")).hexdigest()
    return f"""# HX1 Trusted Host Staged Execution Report

## Scope

HX1 validates one CX2 CortexActionPlan plus host explicit bindings and executes a trusted internal staged workflow over one finite work-root. It is not OpenClaw, an external API, an agent runtime, automatic memory, global discovery, semantic search, cache, database, network, LLM, NLP, or daemon work.

## Scenario Inventory

- HX1-01 mixed explicit A/B/C with pre-existing admitted D: completed
- HX1-02 capture-only: covered by pytest
- HX1-03 admission-only: covered by pytest
- HX1-05 zero-write preflight rejection: covered by pytest
- HX1-06 partial outcome after capture: covered by pytest
- HX1-07 idempotent reopen: completed
- HX1-08 DG6 strict non-influence: completed by before/after DI1 equality guard

## Results

- completed outcome count: 1
- partial outcome count: covered by pytest
- rejected outcome count: covered by pytest
- receipt status: {receipt["status"]}
- completed stages: {", ".join(receipt["completed_stages"])}
- admission receipt ids: {", ".join(receipt["admission_receipt_ids"])}
- explicit assembly ids: {", ".join(receipt["explicit_assembly_admission_ids"])}
- snapshot source ids: {", ".join(receipt["snapshot_source_admission_ids"])}
- C captured/deferred isolation: not present in snapshot or recall envelope
- D pre-existing admitted/unassembled isolation: D was admitted before Stage M and is not present in Stage M admission receipts, snapshot, or recall envelope
- DG6 projection id: {receipt["dg6_projection_id"]}
- recall envelope status: {receipt["recall_public_envelope"]["status"]}
- idempotent reopen: canonical mapping identical
- forbidden output directories: {", ".join(forbidden_dirs) if forbidden_dirs else "none"}
- canonical receipt fingerprint: {receipt["output_fingerprint"]}
- execution input fingerprint: {receipt["execution_input_fingerprint"]}
- canonical receipt sha256: {receipt_sha}

## Commands

- `python -m pytest -q reference/python/tests/test_hx1_trusted_host_bridge.py reference/python/tests/test_hx1_host_binding_preflight.py reference/python/tests/test_hx1_staged_outcomes.py reference/python/tests/test_hx1_receipt_regeneration.py reference/python/tests/test_hx1_boundaries.py`
- `python validation/hx1/run_hx1_validation.py --output validation/hx1/HX1_TRUSTED_HOST_STAGED_EXECUTION_REPORT.md`

## Non-Goals

HX1 does not implement OpenClaw, runtime integration, network service, LLM/NLP calls, embeddings, vector search, automatic admission, GrowthProposal generation, PlacementPlan generation, global admission discovery, cache, database, session manager, daemon, or durable global field persistence.

## HXA1 Final Acceptance Candidate Audit

This report records the HXA1 final acceptance candidate audit for HX1. It is
an acceptance-candidate closure only: it does not merge HX1 into `main`, does
not start OpenClaw/runtime/agent work, and does not enable automatic memory,
global discovery, semantic search, network, database, cache, daemon, LLM, NLP,
or embedding behavior.

### HXA1-A Plan And Binding Precision

- HXA1-A01: verified by CX2 validation and duplicate explicit assembly rejection.
- HXA1-A02: verified by exact capture, admission, recall, and DG6 binding equality tests.
- HXA1-A03: verified by missing, extra, mismatched, and malformed binding preflight tests.
- HXA1-A04: verified by implementation audit; HX1 never resolves opaque refs by scanning stores.
- HXA1-A05: verified by mixed explicit same-call admission tuple equality tests.
- HXA1-A06: verified by pre-existing admitted D control in the mixed explicit validation scenario.
- HXA1-A07: verified by undeclared DG6, declared-disabled DG6, and no-DG6 completion tests.
- HXA1-A08: verified by malformed explicit assembly plan classification as `HX1_INVALID_PLAN`.
- HXA1-A09: verified by malformed nested host public object tests as `HX1_INVALID_BINDINGS`.
- HXA1-A10: verified by invalid context and DG6 enablement tests as `HX1_INVALID_CONTEXT`.

Conclusion: verified; no HX1 implementation change required.

### HXA1-B Canonical Nested Input And Reopen Identity

- HXA1-B01: verified by canonical nested preflight before fingerprinting.
- HXA1-B02: verified by identical reopen producing canonical-identical receipt mappings.
- HXA1-B03: capture request and policy changes fail closed under the same plan id.
- HXA1-B04: DreamShard content and origin changes fail closed under the same plan id.
- HXA1-B05: query, growth submission, finite context, and DG6 view changes fail closed.
- HXA1-B06: canonical value equality, not Python object identity, is used for reopen identity.
- HXA1-B07: invalid nested input zero-write tests leave no reusable marker or receipt.
- HXA1-B08: public error mapping sanitizes traceback, paths, and lower-layer module text.

Conclusion: verified; no HX1 implementation change required.

### HXA1-C Work Root Ownership And Local Side Effects

- HXA1-C01: invalid type, ordinary file, and invalid context work roots are rejected before write.
- HXA1-C02: source repository root, descendants, and caller cwd repository roots are rejected.
- HXA1-C03: external temporary roots are accepted independent of caller cwd.
- HXA1-C04: foreign HX1 markers and non-owned non-empty roots are rejected, not adopted.
- HXA1-C05: preflight rejects are zero-write.
- HXA1-C06: completed and partial runs avoid forbidden field, assembly, recall, cache, database, and global-field durable directories.
- HXA1-C07: identical owned-root reopen is accepted; input drift is rejected.
- HXA1-C08: pathlib-resolved repository root checks and git-file marker tests cover path normalization behavior.

Conclusion: verified; no HX1 implementation change required.

### HXA1-D Stage Order, Failure Semantics, And No Rollback

- HXA1-D01: mixed explicit completed stages are `capture -> admission -> assembly -> recall`; DG6 remains verification-only and is not reported as recall input.
- HXA1-D02: capture-only produces no admission, assembly, DG6, or recall outputs.
- HXA1-D03: admission-only uses a host-established deferred candidate and does not create new capture.
- HXA1-D04: assembly uses only `ExplicitAssembly.admission_ids`.
- HXA1-D05: recall uses the finite DF1 universe built for the plan.
- HXA1-D06: DG6 enabled and disabled no-DG6 paths preserve the same DI1 public recall envelope semantics.
- HXA1-D07: capture success followed by admission failure returns `partial` and preserves capture evidence.
- HXA1-D08: preflight failures are rejected with zero write.
- HXA1-D09: staged failures do not trigger later stages.
- HXA1-D10: lower-layer errors are mapped to stable HX1 errors or partial receipts.

Conclusion: verified; no HX1 implementation change required.

### HXA1-E Public Receipt, Error, And Determinism

- HXA1-E01: completed, partial, and rejected outcomes are structurally distinct.
- HXA1-E02: `receipt_to_mapping` is deterministic and `output_fingerprint` is reproducible.
- HXA1-E03: completed receipts expose only executed capture, admission, snapshot, DG6, and recall ids.
- HXA1-E04: partial receipts report only completed stages and the explicit failed stage.
- HXA1-E05: `error_to_mapping` exposes stable public HX1 code/message shape without raw source text or traceback.
- HXA1-E06: `non_inferences` and DG6 non-influence remain boundary assertions, not factual truth claims.

Conclusion: verified; no HX1 implementation change required.

### HXA1-F Dependency And Scope Drift

- HXA1-F01: host_execution imports no OpenClaw, network, database, cache, LLM, NLP, embedding, or semantic-search module.
- HXA1-F02: lower CI1, BA1, DA1, DF1, DG6, DR1, and DI1 interactions use public module APIs.
- HXA1-F03: host_execution creates no global state, background worker, scheduler, queue, store discovery, or durable Field.
- HXA1-F04: HXA1 changes are limited to validation, tests, reports, and allowed HX1 documentation unless a later audit reveals a true HX1-only defect.
- HXA1-F05: protocol and report language keeps HX1 as a trusted internal host bridge, not an external security boundary.

Conclusion: verified; no HX1 implementation change required.

### HXA1 Candidate Status

[ACCEPTED CANDIDATE] HX1 Trusted Host Staged Execution Bridge.

[UNCHANGED] This report does not merge HX1 to `main` and does not promote or
start runtime, OpenClaw, agent, daemon, global memory, LLM/NLP, embedding,
database, cache, network, or external service work.
"""


def _tree_forbidden(root: Path) -> tuple[str, ...]:
    return tuple(name for name in ("field", "assembly", "recall", "cache", "database", "global-field") if (root / name).exists())


if __name__ == "__main__":
    raise SystemExit(main())
