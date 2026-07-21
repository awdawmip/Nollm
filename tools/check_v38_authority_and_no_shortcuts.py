#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REQUIRED = {
    "AGENTS.md": ("CAOLD Runtime Integrity And Atomic Growth", 2000),
    "docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md": ("数学真值、历史资产复用", 8000),
    "docs/project/ACTIVE_PROJECT.md": ("CAOLD_RUNTIME_INTEGRITY_ATOMIC_GROWTH_IN_PROGRESS", 1000),
    "docs/project/NOLLM_CURRENT_STATUS.md": ("one-cell counterexample", 1000),
    "docs/project/NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md": ("CORE +5%", 2000),
    "docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_11_REV3_PROMPT_BOUNDED_LENS_CARTOGRAPHY_RELATION_ENTRY_RECALL_20260718.md": ("Prompt-bounded", 5000),
    "docs/project/NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md": ("V3.9", 4000),
    "docs/project/tasks/NOLLM_C_A_O_L_D_RUNTIME_INTEGRITY_ATOMIC_PROPOSITION_GROWTH_EVIDENCE_CLOSURE_TASK_20260721.md": ("Gate D", 8000),
    "docs/project/CAOLD_RUNTIME_INTEGRITY_ATOMIC_PROPOSITION_GROWTH_REPORT.md": ("Recall Counterexample", 3000),
    "EVIDENCE.md": ("Active Evidence", 500),
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
    print("Current authority and no-shortcut checks passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
