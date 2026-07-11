from __future__ import annotations

import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGES = {
    "nollm_core": "nollm-core",
    "nollm_snapshot": "nollm-snapshot",
    "nollm_trace": "nollm-trace",
    "nollm_access": "nollm-access",
    "nollm_history": "nollm-history",
    "nollm_audit": "nollm-audit",
}


def test_all_m0_packages_import_from_their_src_roots() -> None:
    for directory in PACKAGES.values():
        sys.path.insert(0, str(ROOT / "packages" / directory / "src"))

    for module in PACKAGES:
        assert importlib.import_module(module).__name__ == module
