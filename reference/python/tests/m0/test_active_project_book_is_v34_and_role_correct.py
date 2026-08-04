from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ARCHITECTURE = ROOT / "docs/architecture/NOLLM_ARCHITECTURE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_DEFERRED_NEURAL_ADAPTER_20260804.md"
ROUTE = ROOT / "docs/project/NOLLM_ROUTE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_20260804.md"
TASK = ROOT / "docs/project/tasks/NOLLM_A_O_L_D_DIRECT_ENCOUNTER_ACTIVATION_PROVIDER_LIVE_GITHUB_EXECUTION_TASK_20260804.md"


def test_active_project_route_is_v313_and_role_correct() -> None:
    basis = (ROOT / "docs/project/ACTIVE_PROJECT.md").read_text(encoding="utf-8")
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    route = ROUTE.read_text(encoding="utf-8")
    assert ARCHITECTURE.name in basis
    assert ROUTE.name in basis
    assert TASK.name in basis
    assert "V3.13 Rev1" in architecture
    assert "Direct Encounter Activation" in route
    assert "FieldEncounterResult" in architecture
    assert "current Statement" in route
    assert "Packet" in architecture
