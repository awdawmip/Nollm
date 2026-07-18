from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter


MESSAGES = (
    ("t0", "请记住：2026年7月18日，我计划下午三点开始东京浅草之旅，并会根据当天降雨情况调整安排。"),
    ("tokyo-1", "关于这次东京之旅，我把第一站定在浅草寺，随后前往东京站。"),
    ("tokyo-2", "这次东京行程里，如果浅草临时关闭，我会直接改去东京站。"),
    ("time-1", "这次东京之旅的集合时间是2026年7月18日下午三点。"),
    ("time-2", "我会在下午两点四十五分到达集合点，为三点出发预留十五分钟。"),
    ("weather-1", "这次东京之旅当天预报有阵雨，我决定随身携带蓝色雨伞。"),
    ("weather-2", "如果东京阵雨持续到傍晚，我会把户外行程改到室内展馆。"),
    ("unrelated-1", "另一个无关事项：审计日志的保留期是三十天。"),
    ("unrelated-2", "关于审计工作，数据库备份固定在每周日凌晨两点执行。"),
)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run(openclaw: Path, evidence: Path) -> list[dict[str, object]]:
    records = []
    for index, (label, message) in enumerate(MESSAGES, 1):
        session_id = f"v311r3-live-{label}-20260718"
        started = perf_counter()
        completed = subprocess.run(
            [
                str(openclaw), "agent", "--agent", "main", "--session-id", session_id,
                "--message", message, "--json", "--timeout", "240",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        records.append({
            "record_type": "live_chat",
            "label": label,
            "sequence": index,
            "session_id": session_id,
            "message_utf8": message,
            "message_sha256": _sha(message),
            "exit_code": completed.returncode,
            "elapsed_ms": round((perf_counter() - started) * 1000, 3),
            "stdout": completed.stdout,
            "stdout_sha256": _sha(completed.stdout),
            "stderr": completed.stderr,
            "stderr_sha256": _sha(completed.stderr),
        })
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_bytes(b"".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
            for item in records
        ))
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--openclaw", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    records = run(args.openclaw, args.evidence)
    print(json.dumps({
        "chat_count": len(records),
        "process_success_count": sum(item["exit_code"] == 0 for item in records),
        "max_elapsed_ms": max(item["elapsed_ms"] for item in records),
    }, sort_keys=True))
    return 0 if all(item["exit_code"] == 0 for item in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
