from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONSTITUTION = ROOT / "protocol" / "v2" / "LAYER_CONSTITUTION.md"
ROOT_DOCS = [
    ROOT / "README.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "ROADMAP.md",
    ROOT / "AGENTS.md",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_layer_constitution_names_all_layers_and_direction() -> None:
    text = read(CONSTITUTION)

    for layer in [
        "L0 Constitution and Protocol",
        "L1 Evidence and Identity Kernel",
        "L2 Deterministic Domain Services",
        "L3 Core Workflow",
        "L4 Host Contract and Execution Bridge",
        "L5 Host Adapter Family",
        "L6 Terminal and Product",
        "L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0",
    ]:
        assert layer in text


def test_layer_constitution_separates_business_paths_from_layers() -> None:
    text = read(CONSTITUTION)

    assert "Capture, Admission, and Assembly are business paths, not layers" in text
    assert "Core facts" in text
    assert "Adapters translate" in text
    assert "Terminals present" in text


def test_identity_and_component_boundaries_are_normative() -> None:
    text = read(CONSTITUTION)

    for phrase in [
        "real evidence identity",
        "host request ID",
        "terminal message ID",
        "CX2 projection reference",
        "HCG1 is an accepted L5 File Capture Adapter",
        "HAG1-C1R is an accepted but unpromoted L5 File Admission Adapter",
        "HX1 and CX2 are L4 assets",
        "DC1 is a deterministic Cortex compiler component",
        "external Cortex policy is model-side policy",
        "OpenClaw legacy is a frozen L5/L6 migration asset",
    ]:
        assert phrase in text


def test_root_navigation_declares_v2_as_only_active_architecture() -> None:
    for path in ROOT_DOCS:
        text = read(path)
        assert "V2 is the only active architecture" in text
        assert "protocol/v2" in text
        assert "only active protocol root" in text
        assert "OpenClaw" in text
        assert "frozen L5/L6 migration asset" in text
        assert "retired history" in text
        assert "L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0" in text


def test_root_navigation_excludes_v1_operation_manuals() -> None:
    forbidden = (
        "Nollm V1 Route Lock",
        "Stable historical V1 tool actions",
        "nollm.cli",
        "examples/openclaw",
    )
    for path in ROOT_DOCS:
        text = read(path)
        offenders = [phrase for phrase in forbidden if phrase in text]

        assert offenders == [], f"{path} reintroduced V1 active navigation: {offenders}"
