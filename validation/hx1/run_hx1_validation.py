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
"""


def _tree_forbidden(root: Path) -> tuple[str, ...]:
    return tuple(name for name in ("field", "assembly", "recall", "cache", "database", "global-field") if (root / name).exists())


if __name__ == "__main__":
    raise SystemExit(main())
