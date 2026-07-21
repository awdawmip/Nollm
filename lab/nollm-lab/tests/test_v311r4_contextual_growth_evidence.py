from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/evidence/verify_v311r4_contextual_growth_evidence.py"


def _module():
    spec = spec_from_file_location("v311r4_contextual_evidence", SCRIPT)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_frozen_contextual_growth_evidence_is_canonical_and_complete() -> None:
    result = _module().verify_payloads(
        (ROOT / "validation/aold_contextual_relational_growth_20260721.jsonl").read_bytes(),
        (ROOT / "validation/aold_contextual_relational_growth_summary_20260721.json").read_bytes(),
    )
    assert result["passed"] is True
    assert all(result["checks"].values())


def test_verifier_rejects_workspace_byte_drift() -> None:
    module = _module()
    evidence = (ROOT / "validation/aold_contextual_relational_growth_20260721.jsonl").read_bytes()
    summary = (ROOT / "validation/aold_contextual_relational_growth_summary_20260721.json").read_bytes()
    result = module.verify_payloads(evidence.replace(b'"passed":true', b'"passed":false', 1), summary)
    assert result["passed"] is False
    assert result["checks"]["all_gates_passed"] is False
