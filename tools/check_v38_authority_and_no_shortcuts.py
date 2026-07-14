#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REQUIRED = {
    "AGENTS.md": ("Reuse before rebuild", 2000),
    "docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md": ("数学真值、历史资产复用", 8000),
    "docs/project/ACTIVE_PROJECT.md": ("IN_PROGRESS", 1000),
    "docs/project/NOLLM_CURRENT_STATUS.md": ("translation-covariant", 1000),
    "docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md": ("CORE +10%", 1000),
    "docs/architecture/NOLLM_ARCHITECTURE_BOOK_V3_8_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_20260714.md": ("平移协变", 5000),
    "docs/project/NOLLM_ROUTE_BOOK_V3_8_TRANSLATION_COVARIANT_COVERAGE_REUSE_20260714.md": ("历史数学资产复用", 4000),
    "docs/project/tasks/NOLLM_C_A_O_L_D_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_REUSE_TASK_20260714.md": ("任务推进向量", 8000),
    "docs/validation/NOLLM_REUSABLE_GEOMETRY_ASSET_INVENTORY_20260714.md": ("REUSE_AS_ORACLE", 3000),
    "docs/validation/NOLLM_INDEPENDENT_GEOMETRY_ORACLE_CONTRACT_20260714.md": ("Oracle A", 2500),
}

FORBIDDEN_PRODUCTION_TOKENS = (
    "select_entries",
    "selected_entries_limit",
    "per_entry_core_recall",
)

def main() -> int:
    root = Path.cwd()
    failures = []
    for rel, (marker, minimum) in REQUIRED.items():
        path = root / rel
        if not path.is_file():
            failures.append(f"missing authority: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.encode("utf-8")) < minimum:
            failures.append(f"authority appears truncated: {rel}")
        if marker not in text:
            failures.append(f"authority marker missing in {rel}: {marker}")
    production_roots = [
        root / "packages",
        root / "integrations/openclaw/formation-loop/python",
        root / "integrations/openclaw/formation-loop/src",
    ]
    for prod in production_roots:
        if not prod.exists():
            continue
        for path in prod.rglob("*"):
            if path.suffix not in {".py", ".ts", ".js", ".json"} or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in FORBIDDEN_PRODUCTION_TOKENS:
                if token in text:
                    failures.append(f"forbidden multi-entry token {token}: {path.relative_to(root)}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("V3.8 authority and no-shortcut checks passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
