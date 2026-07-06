from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ROOT_DOCS = (
    ROOT / "README.md",
    ROOT / "ARCHITECTURE.md",
    ROOT / "ROADMAP.md",
    ROOT / "AGENTS.md",
)
V1_RETIREMENT = ROOT / "docs" / "history" / "V1_RETIREMENT_RECORD.md"
DREAM_GEOMETRY = ROOT / "reference" / "python" / "nollm" / "dream_geometry"

FORBIDDEN_ACTIVE_NAVIGATION = (
    "Nollm V1 Route Lock",
    "Stable historical V1 tool actions",
    "nollm.validate",
    "nollm.orient",
    "nollm.surface",
    "nollm.focus",
    "nollm.recall",
    "nollm.read_card",
    "nollm.write_card",
    "nollm.cli",
    "examples/openclaw",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_v1_route_is_locked_out_of_active_navigation() -> None:
    """V1 route is locked out of active navigation, not locked in as current."""

    for path in ROOT_DOCS:
        text = read(path)
        offenders = [phrase for phrase in FORBIDDEN_ACTIVE_NAVIGATION if phrase in text]

        assert offenders == [], f"{path} reintroduced V1 active navigation: {offenders}"


def test_root_docs_classify_v2_as_active_and_v1_as_retired() -> None:
    for path in ROOT_DOCS:
        text = read(path)

        assert "V2 is the only active architecture" in text
        assert "protocol/v2" in text
        assert "only active protocol root" in text
        assert "retired history" in text
        assert "V1 / MT1 / pre-V2 prototype source remains physically present as retired history" in text
        assert "L6 -> L5 -> L4 -> L3 -> L2 -> L1 -> L0" in text


def test_v1_retirement_record_is_boundary_not_operation_manual() -> None:
    text = read(V1_RETIREMENT)

    assert "may remain physically present temporarily" in text
    assert "Git history is the canonical full archive" in text
    assert "V1 compatibility imports must not enter V2 Core" in text
    assert "not active API" in text
    assert "not active runtime authority" in text
    assert "Nollm V1 Route Lock" not in text
    assert "Stable historical V1 tool actions" not in text


def test_v1_presence_does_not_create_v2_core_compatibility_imports() -> None:
    offenders: list[str] = []
    forbidden = ("nollm.cli", "tools.nollm_tool_manifest", "integrations.openclaw")
    for path in DREAM_GEOMETRY.rglob("*.py"):
        text = read(path)
        for phrase in forbidden:
            if phrase in text:
                offenders.append(f"{path.relative_to(ROOT).as_posix()} contains {phrase}")

    assert offenders == []
