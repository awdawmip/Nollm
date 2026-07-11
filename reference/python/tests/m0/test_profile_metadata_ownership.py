from pathlib import Path

import nollm_core


ROOT = Path(__file__).resolve().parents[4]


def test_research_profile_metadata_is_lab_owned() -> None:
    core_source = (ROOT / "packages/nollm-core/src/nollm_core/profiles.py").read_text(encoding="utf-8")
    lab_source = (ROOT / "lab/nollm-lab/geometry/research_profiles.py").read_text(encoding="utf-8")
    for field in ("role", "scale_model", "rotation_model", "description"):
        assert field not in core_source
        assert field in lab_source
    assert "Profile" not in nollm_core.__all__
    assert "available_profile_ids" in nollm_core.__all__
    assert "runtime_profile" in nollm_core.__all__
