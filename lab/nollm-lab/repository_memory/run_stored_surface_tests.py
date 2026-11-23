"""Run the focused stored-Surface, content-budget and existing field regressions."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"),
               str(ROOT / "packages/nollm-access/src"), str(Path(__file__).parent)]
FILES = (
    "packages/nollm-access/tests/test_content_budget.py",
    "packages/nollm-access/tests/test_surface_page_content_reads.py",
    "packages/nollm-access/tests/test_experimental_multilayer_write.py",
    "lab/nollm-lab/repository_memory/test_stored_surface_encounter.py",
    "lab/nollm-lab/repository_memory/test_project_encounter.py",
    "lab/nollm-lab/repository_memory/test_project_pressure.py",
    "lab/nollm-lab/repository_memory/test_project_memory.py",
)


def main():
    suite = unittest.TestSuite()
    for relative in FILES:
        path = ROOT / relative
        suite.addTests(unittest.TestLoader().discover(str(path.parent),pattern=path.name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
