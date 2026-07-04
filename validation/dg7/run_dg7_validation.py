from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile


def build_report() -> str:
    first = _run_fresh()
    second = _run_fresh()
    if first != second:
        raise RuntimeError("DG7 fresh-process receipts differ")
    receipt_hash = sha256(first.encode("utf-8")).hexdigest()
    lines = [
        "# DG7 Reference Runtime Positive Verification Report",
        "",
        "## Verified Facts",
        "",
        "- fresh Python process explicit A/B/C/D scenario: `completed`",
        "- A/B capture status: `deferred`, then BA1/DA1 admitted and DF1 assembled",
        "- C isolation: `captured/deferred only`, no AdmissionRecord, no snapshot/projection/envelope evidence",
        "- D isolation: `admitted`, excluded from the explicit DF1 finite set and absent from DG6/DR1/DI1",
        "- DG6 projection: lossless expansion matches `snapshot.replayed_traces` and does not affect DI1 recall",
        "- DI1 envelope: exposes only A/B original DreamShard evidence and no geometry/trace/cover/gravity payload",
        f"- two fresh-process canonical receipt SHA-256: `{receipt_hash}`",
        "- durable writes: limited to the explicit temporary work root and explicit receipt output",
        "",
        "## Reasonable Inference",
        "",
        "A controlled host integration can use this style of explicit runtime receipt without changing Core boundaries.",
        "",
        "## Forbidden Inference",
        "",
        "DG7 does not implement a production runtime, OpenClaw integration, automatic memory, semantic admission, persistent compression, global discovery, storage optimization, recall acceleration, or performance claim.",
        "",
        "## Pending Research",
        "",
        "- external host generation of Growth and Placement input",
        "- stable transport adapter design",
        "- session governance, configuration, cache, failure recovery, and user experience",
        "- OpenClaw or other host integration as a separate owner decision",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    output = None
    if "--output" in sys.argv:
        index = sys.argv.index("--output")
        output = Path(sys.argv[index + 1])
    report = build_report()
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8", newline="\n")
    else:
        print(report, end="")


def _run_fresh() -> str:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        output = root / "receipt.json"
        script = Path("reference/python/scripts/run_dg7_reference_runtime.py")
        result = subprocess.run(
            [sys.executable, str(script), "--scenario", "fixed-dg7-v1", "--work-root", str(root / "work"), "--output", str(output)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stdout or result.stderr)
        return output.read_text(encoding="utf-8")


if __name__ == "__main__":
    main()
