from hashlib import sha256
from pathlib import Path
import sys

from nollm.grf.cell_address import CellAddress
from nollm.grf.coverage_template import CoverageTemplateCompiler as LegacyCompiler, expand_template as legacy_expand
from nollm.grf.profiles import get_profile as legacy_profile
from nollm_core import GeometryAddress, KernelRegistry, expand_template, runtime_profile


GEOMETRY_LAB = Path(__file__).resolve().parents[1] / "geometry"
sys.path.insert(0, str(GEOMETRY_LAB))
from compiler import CoverageTemplateCompiler  # noqa: E402
from generate_compiled_templates import canonical_document  # noqa: E402
from research_profiles import research_profile  # noqa: E402


def template_contract(template):
    return {
        "identity": (template.profile_id, template.direction, template.from_layer_mod, template.to_layer_mod, template.source_phase),
        "entries": tuple((e.layer_delta, e.dq, e.dr, e.weight_q16, e.kernel_type, e.flags) for e in template.entries),
        "weights": (template.sum_weight_q16, template.normalization_residual_q16, template.approximation_residual_q16),
        "compiler": template.compiler.to_mapping() if hasattr(template.compiler, "to_mapping") else {**template.compiler, "flags": list(template.compiler["flags"])},
    }


def profile_contract(profile):
    return tuple(getattr(profile, name) for name in ("profile_id", "role", "coordinate_model", "scale_model", "rotation_model", "weight_format", "runtime_polygon", "runtime_float_allowed", "description"))


def main() -> None:
    registry = KernelRegistry()
    generated = canonical_document()
    assert sha256(generated).hexdigest() == registry.compiled_artifact_sha256
    legacy, active = LegacyCompiler(), CoverageTemplateCompiler()
    count = 0
    for profile_id in ("eisenstein_exact_v1", "aligned_baseline_v1", "dream_quasi_v1"):
        assert profile_contract(research_profile(profile_id)) == profile_contract(legacy_profile(profile_id))
        runtime = runtime_profile(profile_id)
        assert (runtime.profile_id, runtime.coordinate_model, runtime.weight_format) == (
            research_profile(profile_id).profile_id,
            research_profile(profile_id).coordinate_model,
            research_profile(profile_id).weight_format,
        )
        for direction in ("coverage_up", "coverage_down", "lateral"):
            old = legacy.compile(profile_id, direction, 3, "phase:x")
            new = active.compile(profile_id, direction, 3, "phase:x")
            assert template_contract(new) == template_contract(old)
            old_cell = CellAddress(profile_id, "chart", 3, -4, 2, "phase:x")
            new_cell = GeometryAddress(profile_id, "chart", 3, -4, 2, "phase:x")
            old_expanded = tuple((cell.stable_key(), weight) for cell, weight in legacy_expand(old_cell, old))
            public_template = registry.coverage_template(profile_id, direction)
            assert new.to_mapping() == public_template.to_mapping() | {"from_layer_mod": 3, "to_layer_mod": 3 + (-1 if direction == "coverage_up" else 1 if direction == "coverage_down" else 0), "source_phase": "phase:x"}
            new_expanded = tuple((cell.stable_key(), weight) for cell, weight in expand_template(new_cell, public_template))
            assert new_expanded == old_expanded
            count += 1
    print(f"geometry full parity: {count}/9 templates passed")


if __name__ == "__main__":
    main()
