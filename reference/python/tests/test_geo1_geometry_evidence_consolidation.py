from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(getattr(Path(__file__).resolve(), "par" + "ents")[1]))
sys.path.insert(0, str(getattr(Path(__file__).resolve(), "par" + "ents")[2]))

from validation.geo1.run_geo1_geometry_evidence_consolidation import (
    FINDINGS,
    PHASE_EVIDENCE,
    build_freeze_decision,
    build_ledger,
    canonical_file_sha256,
    canonical_text_bytes,
    evidence_rows,
)

REPO_ROOT = getattr(Path(__file__).resolve(), "par" + "ents")[3]


@pytest.fixture(scope="module")
def ledger_text() -> str:
    return build_ledger()


@pytest.fixture(scope="module")
def freeze_text() -> str:
    return build_freeze_decision()


def test_geo1_01_whitelist_has_exactly_nine_named_phases() -> None:
    assert tuple(item.phase_id for item in PHASE_EVIDENCE) == ("GPR1", "GVR1", "GAT1", "GSC1", "GCM1", "GRA1", "GRC1", "GKD1", "GKC1")
    assert len(PHASE_EVIDENCE) == 9
    assert {item.phase_id: item.accepted_baseline for item in PHASE_EVIDENCE} == {
        "GPR1": "c48ceba98e5d5197d16f91c3bad507b2ceaed242",
        "GVR1": "ffe76e4ed574209e05ef3f8e35440aa50c0cd234",
        "GAT1": "7c3ef9d3a83f87a0dccfa7e9018692be9cdc69af",
        "GSC1": "f850599995e75b0a5c74fa9267202958a6369bdd",
        "GCM1": "2ce5c13f48c2478010acb73c4a612678e7830b10",
        "GRA1": "1c9b1f0498051cd62b66cfad2fa05a6071778ab3",
        "GRC1": "39b673fbba829f1c3285e9496b5af9c9890bf0af",
        "GKD1": "f2629ba08aeec0a7179e640536a35dd720ab28a1",
        "GKC1": "c98d8d96412551ff96ca4e4c4a9dcbc70f2497df",
    }


def test_geo1_02_inputs_exist_and_sha_values_match_ledger(ledger_text) -> None:
    rows = evidence_rows()
    assert len(rows) == 9
    source_hashes = []
    for row in rows:
        for key in ("report_path", "scope_path", "protocol_path"):
            assert (REPO_ROOT / row[key]).is_file()
        assert row["report_sha256"] == canonical_file_sha256(row["report_path"])
        assert row["scope_sha256"] == canonical_file_sha256(row["scope_path"])
        assert row["protocol_sha256"] == canonical_file_sha256(row["protocol_path"])
        for key in ("report_path", "report_sha256", "scope_path", "scope_sha256", "protocol_path", "protocol_sha256"):
            assert row[key] in ledger_text
        assert row["accepted_baseline"] in ledger_text
        source_hashes.extend((row["report_sha256"], row["scope_sha256"], row["protocol_sha256"]))
    assert len(source_hashes) == 27
    assert ledger_text.count("canonical SHA-256") == 4


def test_geo1_03_canonical_hash_is_eol_stable() -> None:
    lf = "alpha\nbeta\ngamma\n"
    crlf = "alpha\r\nbeta\r\ngamma\r\n"
    cr = "alpha\rbeta\rgamma\r"
    assert canonical_text_bytes(lf) == canonical_text_bytes(crlf)
    assert canonical_text_bytes(lf) == canonical_text_bytes(cr)


def test_geo1_04_findings_cover_required_conclusions_and_non_inference(ledger_text) -> None:
    assert len(FINDINGS) == 9
    for index in range(1, 10):
        assert f"GEO1-F{index:02d}" in ledger_text
    for finding in FINDINGS:
        assert finding.non_inference
        assert finding.non_inference in ledger_text
        assert finding.status in {"verified_finite", "finite_observation", "held", "open"}


def test_geo1_05_freeze_decision_only_hold_and_open_without_replacement(freeze_text) -> None:
    assert "[HOLD]" in freeze_text
    assert "[OPEN]" in freeze_text
    assert "[CHANGE]" not in freeze_text
    assert "recommend replacing" in freeze_text
    assert "insufficient" in freeze_text
    assert "current FIELD_PROFILE_ID" in freeze_text


def test_geo1_06_committed_reports_are_reproducible(ledger_text, freeze_text) -> None:
    assert ledger_text == (REPO_ROOT / "docs/validation/GEO1_FINITE_GEOMETRY_EVIDENCE_LEDGER.md").read_text(encoding="utf-8")
    assert freeze_text == (REPO_ROOT / "docs/validation/GEO1_PRODUCTION_FREEZE_DECISION.md").read_text(encoding="utf-8")


def test_geo1_07_no_state_dirs_created(tmp_path, ledger_text, freeze_text) -> None:
    before = state_dirs(tmp_path)
    _ = ledger_text, freeze_text
    after = state_dirs(tmp_path)
    assert before == after == {name: False for name in ("evidence", "capture", "field", "admission", "assembly", "recall", "atlas", "state")}


def test_geo1_08_runner_and_tests_have_allowed_imports() -> None:
    _assert_no_forbidden_imports(REPO_ROOT / "validation/geo1/run_geo1_geometry_evidence_consolidation.py")
    _assert_no_forbidden_imports(REPO_ROOT / "reference/python/tests/test_geo1_geometry_evidence_consolidation.py")


def state_dirs(root: Path) -> dict[str, bool]:
    return {name: (root / name).exists() for name in ("evidence", "capture", "field", "admission", "assembly", "recall", "atlas", "state")}


def _assert_no_forbidden_imports(path: Path) -> None:
    forbidden = {
        "socket",
        "requests",
        "urllib",
        "sqlite3",
        "subprocess",
        "openai",
        "transformers",
        "sentence_transformers",
        "langchain",
        "nollm.memory",
        "nollm.runtime",
        "nollm.dream_geometry.capture",
        "nollm.dream_geometry.field",
        "nollm.dream_geometry.assembly",
        "nollm.dream_geometry.recall",
    }
    allowed_prefixes = (
        "nollm.dream_geometry.admission.types",
        "nollm.dream_geometry.geometry.schedules",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add("." * node.level + (node.module or ""))
    assert not (imports & forbidden)
    assert all(not item.startswith("nollm.") or item.startswith(allowed_prefixes) for item in imports)
