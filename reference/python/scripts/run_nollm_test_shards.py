from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True

REFERENCE_PYTHON = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
TAIL_CHARS = 4000

PROFILE_TESTS = {
    "dream": (
        "tests/test_dream_*.py",
        "tests/test_cluster_pressure.py",
        "tests/test_scale_scan_traversal.py",
        "tests/test_parameter_experiments.py",
        "tests/test_openclaw_dream_experiment.py",
        "tests/test_local_gate.py",
    ),
    "core": (
        "tests/test_write_read.py",
        "tests/test_recall.py",
        "tests/test_tool_api.py",
        "tests/test_tool_envelope.py",
        "tests/test_status.py",
        "tests/test_validate.py",
        "tests/test_cortex.py",
        "tests/test_history.py",
        "tests/test_audit.py",
        "tests/test_review.py",
        "tests/test_annotations.py",
    ),
    "docs": (
        "tests/test_architecture_language.py",
        "tests/test_context_boundary.py",
        "tests/test_examples.py",
        "tests/test_honeycomb_metadata.py",
        "tests/test_inspection_semantics.py",
        "tests/test_integration_pack.py",
        "tests/test_no_forbidden_features.py",
        "tests/test_package_hygiene_script.py",
        "tests/test_repository_hygiene.py",
        "tests/test_terminology.py",
        "tests/test_v1_docs_consistency.py",
        "tests/test_v1_route_lock.py",
    ),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic internal Nollm pytest shards.")
    parser.add_argument("--profile", choices=("collect", "dream", "core", "docs", "full"), required=True)
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root path.")
    parser.add_argument("--timeout", type=float, default=120.0, help="Subprocess timeout in seconds.")
    parser.add_argument("--output", default=None, help="Output JSON path.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    reference_python = repo_root / "reference" / "python"
    output = (
        Path(args.output).resolve()
        if args.output is not None
        else repo_root / "out" / "nollm_runtime" / "test_shards" / f"{args.profile}.json"
    )
    report = run_test_shard(
        args.profile,
        reference_python=reference_python,
        timeout_seconds=args.timeout,
    )
    write_report(report, output)
    print(
        "wrote nollm test shard report "
        f"path={output} profile={report['profile']} status={report['status']} "
        f"returncode={report['returncode']} timed_out={str(report['timed_out']).lower()}"
    )
    return 0 if report["status"] == "ok" else 1


def run_test_shard(profile: str, *, reference_python: Path, timeout_seconds: float) -> dict[str, object]:
    command, missing = command_for_profile(profile, reference_python)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    started = time.monotonic()
    stdout = ""
    stderr = ""
    returncode = 0
    timed_out = False
    if not command:
        status = "skipped"
        duration = time.monotonic() - started
    else:
        try:
            result = subprocess.run(
                command,
                cwd=reference_python,
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
            )
            stdout = result.stdout
            stderr = result.stderr
            returncode = int(result.returncode)
            status = "ok" if returncode == 0 else "failed"
        except subprocess.TimeoutExpired as exc:
            stdout = _string_output(exc.stdout)
            stderr = _string_output(exc.stderr)
            returncode = -1
            timed_out = True
            status = "timed_out"
        duration = time.monotonic() - started

    return {
        "schema": "nollm.test_shard.v1",
        "status": status,
        "profile": profile,
        "command": command,
        "missing_tests": missing,
        "returncode": returncode,
        "timed_out": timed_out,
        "duration_seconds": round(duration, 3),
        "collected_count": collected_count(stdout),
        "stdout_tail": tail(stdout),
        "stderr_tail": tail(stderr),
    }


def command_for_profile(profile: str, reference_python: Path) -> tuple[list[str], list[str]]:
    if profile == "collect":
        return [sys.executable, "-m", "pytest", "--collect-only", "-q"], []
    if profile == "full":
        return [sys.executable, "run_tests.py"], []
    selected: list[str] = []
    missing: list[str] = []
    for pattern in PROFILE_TESTS[profile]:
        if any(char in pattern for char in "*?[]"):
            matches = sorted(path.relative_to(reference_python).as_posix() for path in reference_python.glob(pattern))
            if matches:
                selected.extend(matches)
            else:
                missing.append(pattern)
            continue
        path = reference_python / pattern
        if path.exists():
            selected.append(pattern)
        else:
            missing.append(pattern)
    if not selected:
        return [], missing
    return [sys.executable, "-m", "pytest", "-q", *selected], missing


def collected_count(stdout: str) -> int:
    matches = re.findall(r"(\d+)\s+tests?\s+collected", stdout)
    if matches:
        return int(matches[-1])
    node_ids = [
        line
        for line in stdout.splitlines()
        if "::" in line and not line.startswith(("=", " "))
    ]
    return len(node_ids)


def tail(text: str) -> str:
    if len(text) <= TAIL_CHARS:
        return text
    return f"... output truncated to last {TAIL_CHARS} chars ...\n{text[-TAIL_CHARS:]}"


def write_report(report: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _string_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
