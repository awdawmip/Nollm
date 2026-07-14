#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EXPECTED = {
    "reference/python/nollm/dream_geometry/geometry/chart.py": "bc7e1f654352d6267eeaef68dadcb248ed21feb194f9623072f852a22bfb86aa",
    "reference/python/nollm/dream_geometry/geometry/hexgrid.py": "13ac2f3b6bc4cede756896f1dca2e0fc41397f284ae3ae123eaa274ab4e317f6",
    "reference/python/nollm/dream_geometry/geometry/polygon.py": "b66866a23d25a2c03c3325a78842cae3414204c40d4025475b965d7727d1a56b",
    "reference/python/nollm/dream_geometry/geometry/coverage.py": "b1c2c7567dfc32f1657210aed7c4276ba25c3cefc108d5cbc9443d5716e572f1",
    "reference/python/nollm/dream_geometry/geometry/schedules.py": "eaa9a56921d3cefda6677369f6502a7520c9d9225e39b731be7aa5ca40422b62",
    "reference/python/nollm/dream_geometry/geometry/transform.py": "7469d112a914131eb5b1e3fcfbb5b01a439198ec1d021ca1f8faf55e6213bcd5",
    "reference/python/nollm/dream_geometry/geometry/metrics.py": "b1e8d729f56cae163f3a8283936d9e6a1b10625e3b458089e60926700d5bd974",
    "reference/python/tests/fixtures/gvr1/fixture.py": "9dc3f2a420e62c605919d9016e7ab783bcd71fcb800f26859b96ca42f36883b1",
    "reference/python/tests/fixtures/gra1/fixture.py": "32001c7781640a921216628269adf3ba29221aef83646ff7f4fec66520e9bccd",
    "reference/python/tests/fixtures/grc1/fixture.py": "cdba107d3c7f6a84c475bcc4a5fb2db301d6b466ae93b12f45a74a15214fcfb6",
    "reference/python/tests/fixtures/gkd1/fixture.py": "e78044e55681b01c7c80b1698702189a285ec380e19b4e85ccebba7d74121c95",
    "reference/python/tests/fixtures/gpr1/fixture.py": "c6c793f0fdde2d57ace75e85c99998c47be73f18d3c6dffe59949687dfdad199",
    "validation/gvr1/run_gvr1_translation_variation.py": "ec320f788b663f1eb80535d6772efd814c7ff5a64e91b494f48a51e1ff1498f2",
    "validation/gra1/run_gra1_rotation_scale_resonance.py": "e592a329fe5ceb9ab1d07c366d5cc7fdb0312b739e9b264934024b8bb333c4ac",
    "validation/grc1/run_grc1_resonance_conditioned_coverage.py": "0d22994c46be10fb1c2a62a2f7f1ff6700cb73910ec7bf042bbfee288eca370a",
    "validation/gkd1/run_gkd1_bidirectional_coverage.py": "3e458f4592c43b1df3609481293c4b177e1929b052901336322fa1aabe0b8226",
    "validation/gpr1/run_gpr1_geometry_profile_regime.py": "76b0e302673e3000cde976ae5987ce4b0eb6da76e30470259ea5efd292de372c",
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main() -> int:
    root = Path.cwd()
    failures = []
    rows = []
    for rel, expected in EXPECTED.items():
        path = root / rel
        if not path.is_file():
            failures.append(f"MISSING {rel}")
            rows.append({"path": rel, "status": "missing", "expected": expected})
            continue
        actual = sha256(path)
        status = "match" if actual == expected else "changed"
        rows.append({"path": rel, "status": status, "expected": expected, "actual": actual})
        if status != "match":
            failures.append(f"CHANGED {rel}: {actual}")
    print(json.dumps({"assets": rows, "failures": failures}, indent=2))
    if failures:
        print("Historical assets differ. Do not discard them; inspect Git provenance and classify changes.", file=sys.stderr)
        return 1
    print("Reusable geometry assets verified.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
