from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HCG_ROOT = ROOT / "reference" / "python" / "nollm" / "dream_geometry" / "host_capture_gateway"


def test_hcg1_11_gateway_source_has_no_hidden_discovery_or_search() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in sorted(HCG_ROOT.glob("*.py")))
    forbidden = (
        ".glob(",
        ".rglob(",
        ".iterdir(",
        "list_all",
        "search",
        "compile_query",
        "resolve_recall",
        "AdmissionRequest(",
        "GrowthProposal",
        "PlacementPlan",
        "OpenClaw",
        "sqlite",
        "requests.",
        "http",
    )
    for token in forbidden:
        assert token not in source
    assert "execute_host_plan(" in source
    assert "CaptureVisibility(" in source


def test_hcg1_12_gateway_is_not_registered_on_v1_cli_or_openclaw_surfaces() -> None:
    cli_source = (ROOT / "reference" / "python" / "nollm" / "cli.py").read_text(encoding="utf-8")
    assert "host_capture_gateway" not in cli_source
    assert "run_nollm_host_capture_gateway" not in cli_source

    tool_api = ROOT / "reference" / "python" / "nollm" / "tool_api.py"
    if tool_api.exists():
        tool_source = tool_api.read_text(encoding="utf-8")
        assert "host_capture_gateway" not in tool_source
        assert "hcg1" not in tool_source.lower()
