from nollm.grf.coverage_template import CoverageTemplateCompiler as LegacyCompiler
from nollm_core import CoverageTemplateCompiler


def entries(template):
    return tuple((entry.layer_delta, entry.dq, entry.dr, entry.weight_q16) for entry in template.entries)


def main() -> None:
    legacy = LegacyCompiler()
    active = CoverageTemplateCompiler()
    for profile_id in ("eisenstein_exact_v1", "aligned_baseline_v1", "dream_quasi_v1"):
        for direction in ("coverage_up", "coverage_down"):
            assert entries(active.compile(profile_id, direction)) == entries(legacy.compile(profile_id, direction))
    print("geometry parity: 6/6 templates passed")


if __name__ == "__main__":
    main()
