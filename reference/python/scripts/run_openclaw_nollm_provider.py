"""CLI entry point for the Nollm OpenClaw memory provider sidecar.

Reads a config object from argv (as JSON), reads a command object from stdin,
and writes a JSON result to stdout. All Python input is via stdin JSON; no
turn content is encoded into argv.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nollm.openclaw_memory_provider_alpha import run_from_stdin  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Nollm OpenClaw memory provider sidecar."
    )
    parser.add_argument(
        "--config-json",
        required=True,
        help="JSON object containing the provider configuration.",
    )
    args = parser.parse_args(argv)

    try:
        config_payload = json.loads(args.config_json)
    except json.JSONDecodeError as exc:
        result = {
            "ok": False,
            "schema": "nollm.provider.error.v1",
            "error": {
                "code": "configuration_error",
                "message": f"--config-json is not valid JSON: {exc}",
                "retryable": False,
            },
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    if not isinstance(config_payload, dict):
        result = {
            "ok": False,
            "schema": "nollm.provider.error.v1",
            "error": {
                "code": "configuration_error",
                "message": "--config-json must be a JSON object",
                "retryable": False,
            },
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    result = run_from_stdin(config_payload)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
