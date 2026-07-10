from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "reference" / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "reference" / "python"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.adapters.grf5_operational_validation import run_operational_validation  # noqa: E402


def main() -> int:
    with TemporaryDirectory(prefix="nollm_grf5_operational_") as directory:
        result = run_operational_validation(Path(directory), cycles=250, restart_interval=25)
    print(json.dumps(result.__dict__, sort_keys=True, indent=2))
    return 0 if result.replay_deterministic and result.source_fallback_preserved else 1


if __name__ == "__main__":
    raise SystemExit(main())
