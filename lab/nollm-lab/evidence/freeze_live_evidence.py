from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import time
from uuid import uuid4


SCHEMA_VERSION = "nollm_live_evidence_freeze_v1"


def _canonical(value: dict[str, object]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def _same_path(left: object, right: Path) -> bool:
    if type(left) is not str or not left:
        return False
    return os.path.normcase(str(Path(left).resolve())) == os.path.normcase(str(right.resolve()))


def _writer_configs(value: object) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    if type(value) is dict:
        if "evidence_path" in value or "debug_trace" in value:
            found.append(value)
        for child in value.values():
            found.extend(_writer_configs(child))
    elif type(value) is list:
        for child in value:
            found.extend(_writer_configs(child))
    return found


def _powershell_json(script: str) -> object:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
        check=False,
    )
    if completed.returncode != 0:
        return {"probe_error": completed.stderr.strip() or f"PowerShell exited {completed.returncode}"}
    output = completed.stdout.strip()
    return [] if not output else json.loads(output)


def _is_gateway_process(process: object) -> bool:
    if type(process) is not dict:
        return False
    name = process.get("Name")
    command_line = process.get("CommandLine")
    if type(name) is not str or name.lower() != "node.exe" or type(command_line) is not str:
        return False
    return re.search(
        r"(?i)(?:openclaw(?:\.mjs)?|openclaw[\\/]dist[\\/]index\.js)\"?\s+gateway(?:\s|$)",
        command_line,
    ) is not None


def windows_gateway_probe(port: int) -> dict[str, object]:
    listeners = _powershell_json(
        f"@(Get-NetTCPConnection -State Listen -LocalPort {port} -ErrorAction SilentlyContinue | "
        "Select-Object LocalAddress,LocalPort,OwningProcess) | ConvertTo-Json -Compress"
    )
    process_probe = _powershell_json(
        "@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | "
        "Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine } | "
        "Select-Object ProcessId,Name,CommandLine) | ConvertTo-Json -Compress"
    )
    candidates = process_probe if type(process_probe) is list else [process_probe]
    processes = [process for process in candidates if _is_gateway_process(process)]
    return {"backend": "windows_powershell_process_api", "port": port, "listeners": listeners, "gateway_processes": processes}


def _snapshot(path: Path) -> dict[str, int]:
    info = path.stat()
    return {"size_bytes": info.st_size, "mtime_ns": info.st_mtime_ns}


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid4().hex}.tmp"
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def freeze_evidence(
    live_path: Path,
    frozen_path: Path,
    plugin_config_path: Path,
    *,
    gateway_port: int = 18789,
    stability_seconds: float = 2.0,
    operator_attestation: dict[str, object] | None = None,
) -> dict[str, object]:
    live = Path(live_path).resolve()
    frozen = Path(frozen_path).resolve()
    config_path = Path(plugin_config_path).resolve()
    if not live.is_file():
        raise FileNotFoundError("live evidence source does not exist")
    if frozen.exists():
        raise FileExistsError("frozen evidence target already exists")
    if "frozen" not in {part.lower() for part in frozen.parts}:
        raise ValueError("frozen evidence target must be under a frozen directory")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    writers = _writer_configs(config)
    active_source = [item for item in writers if item.get("debug_trace") is True and _same_path(item.get("evidence_path"), live)]
    active_frozen = [item for item in writers if item.get("debug_trace") is True and _same_path(item.get("evidence_path"), frozen)]
    if active_source:
        raise RuntimeError("live evidence writer must be rotated or disabled before freeze")
    if active_frozen:
        raise RuntimeError("frozen evidence target is still configured as a writer path")

    before = _snapshot(live)
    gateway_before = windows_gateway_probe(gateway_port)
    time.sleep(stability_seconds)
    after = _snapshot(live)
    if after != before:
        raise RuntimeError("live evidence source changed during freeze stability window")
    payload = live.read_bytes()
    if _snapshot(live) != after:
        raise RuntimeError("live evidence source changed while reading freeze bytes")
    _atomic_write(frozen, payload)
    frozen.chmod(0o444)
    gateway_after = windows_gateway_probe(gateway_port)
    final = frozen.read_bytes()
    if final != payload:
        raise RuntimeError("frozen evidence bytes changed after publication")
    lines = final.splitlines()
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "live_source": str(live),
        "frozen_artifact": str(frozen),
        "bytes": len(final),
        "line_count": len(lines),
        "sha256": sha256(final).hexdigest(),
        "source_stability": {"before": before, "after": after, "seconds": stability_seconds, "stable": True},
        "plugin_config": {
            "path": str(config_path),
            "active_writer_paths": [item.get("evidence_path") for item in writers if item.get("debug_trace") is True],
            "source_writer_active_at_freeze": False,
            "frozen_writer_active_at_freeze": False,
        },
        "gateway_probe_before": gateway_before,
        "gateway_probe_after": gateway_after,
        "operator_attestation": operator_attestation,
    }
    _atomic_write(frozen.with_suffix(frozen.suffix + ".freeze.json"), _canonical(metadata))
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--plugin-config", type=Path, required=True)
    parser.add_argument("--gateway-port", type=int, default=18789)
    parser.add_argument("--stability-seconds", type=float, default=2.0)
    arguments = parser.parse_args()
    print(json.dumps(freeze_evidence(
        arguments.live,
        arguments.frozen,
        arguments.plugin_config,
        gateway_port=arguments.gateway_port,
        stability_seconds=arguments.stability_seconds,
    ), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
