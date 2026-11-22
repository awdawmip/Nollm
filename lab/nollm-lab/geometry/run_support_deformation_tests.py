"""Run the support-pressure and deformation functional slice with stdlib unittest.

Execute from any directory. Tests use temporary fields and Git repositories;
the user's persistent memory and installed skills are not changed.
"""
from pathlib import Path
import sys
import unittest


REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(REPO / "packages/nollm-core/src"),
    str(REPO / "packages/nollm-access/src"),
    str(REPO / "lab/nollm-lab/repository_memory"),
    str(REPO / "lab/nollm-lab"),
    str(REPO / "lab/nollm-lab/geometry"),
]

TEST_FILES = (
    "packages/nollm-core/tests/test_incoming_coverage.py",
    "packages/nollm-core/tests/test_residual_mask_coverage.py",
    "packages/nollm-access/tests/test_support_pressure.py",
    "packages/nollm-access/tests/test_experimental_multilayer_write.py",
    "lab/nollm-lab/repository_memory/test_project_pressure.py",
    "lab/nollm-lab/geometry/tests/test_motion.py",
    "lab/nollm-lab/geometry/tests/test_motion_residual_events.py",
    "lab/nollm-lab/geometry/tests/test_deformation.py",
    "lab/nollm-lab/geometry/tests/test_relative_geometry.py",
    "lab/nollm-lab/geometry/tests/test_pressure_evaluation.py",
    "lab/nollm-lab/geometry/tests/test_pressure_reuse.py",
    "lab/nollm-lab/repository_memory/test_project_encounter.py",
    "lab/nollm-lab/repository_memory/test_project_memory.py",
)


def main():
    suite = unittest.TestSuite()
    for relative in TEST_FILES:
        path = REPO / relative
        suite.addTests(unittest.TestLoader().discover(str(path.parent), pattern=path.name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
