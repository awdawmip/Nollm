from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "reference" / "python", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from integrations.adapters.grf4r_failure_recovery import run_failure_recovery  # noqa: E402
from integrations.adapters.grf4r_host_lifecycle import run_all_host_lifecycles  # noqa: E402
from nollm.grf.readiness_validation import core_readiness  # noqa: E402


def main() -> int:
    with TemporaryDirectory(prefix="nollm_grf4r_readiness_") as directory:
        root = Path(directory)
        hosts = run_all_host_lifecycles(root / "hosts")
        recovery = run_failure_recovery(root / "failure")
    checks = core_readiness()
    checks["hosts_replaceable"] = all(item.retry_idempotent and item.replay_deterministic for item in hosts)
    checks["failure_recoverable"] = recovery.passed
    checks["five_gates_passed"] = all(checks.values())
    print(json.dumps({"status": "GRF_READY_FOR_NEXT_STAGE" if checks["five_gates_passed"] else "GRF_NOT_READY", "checks": checks}, sort_keys=True, indent=2))
    return 0 if checks["five_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
