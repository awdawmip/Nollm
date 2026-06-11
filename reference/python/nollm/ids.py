from __future__ import annotations

import hashlib
import re
from datetime import date
from pathlib import Path


def today_stamp() -> str:
    return date.today().strftime("%Y%m%d")


def today_iso() -> str:
    return date.today().isoformat()


def slugify(text: str) -> str:
    lowered = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    if slug:
        return slug[:48]
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return f"h_{digest}"


def next_sequence(existing: list[str], prefix: str, stamp: str) -> int:
    pattern = re.compile(rf"^{re.escape(prefix)}_{stamp}_(\d{{6}})")
    highest = 0
    for value in existing:
        match = pattern.match(value)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def next_event_id(ledger_path: Path, stamp: str | None = None) -> str:
    stamp = stamp or today_stamp()
    existing: list[str] = []
    if ledger_path.exists():
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            if '"event_id"' in line:
                match = re.search(r'"event_id"\s*:\s*"([^"]+)"', line)
                if match:
                    existing.append(match.group(1))
    return f"evt_{stamp}_{next_sequence(existing, 'evt', stamp):06d}"


def next_recall_id(recalls_dir: Path, stamp: str | None = None) -> str:
    stamp = stamp or today_stamp()
    existing = [path.stem for path in recalls_dir.glob(f"recall_{stamp}_*.json")]
    return f"recall_{stamp}_{next_sequence(existing, 'recall', stamp):06d}"


def card_id_for(title: str, cards_root: Path, stamp: str | None = None) -> str:
    stamp = stamp or today_stamp()
    base = f"card_{stamp}_{slugify(title)}"
    candidate = base
    index = 2
    while any(cards_root.rglob(f"{candidate}.md")):
        candidate = f"{base}_{index}"
        index += 1
    return candidate

