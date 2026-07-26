from __future__ import annotations

import ast
import json
from pathlib import Path
import sys


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    legacy = {"adapter", "dream_adapter", "sculptor", "legacy_bridge"}
    seen: set[str] = set()
    queue = ["bridge"]
    category_terms = {
        "sensitive", "secret", "password", "credential", "medical", "weather",
        "temporary", "tool noise", "no_memory", "question defer",
    }
    category_branches = 0
    source_role_gates = 0
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        path = root / f"{name}.py"
        tree = ast.parse(path.read_text("utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
                child = node.module.split(".", 1)[0]
                if (root / f"{child}.py").exists() and child not in seen:
                    queue.append(child)
            if isinstance(node, (ast.If, ast.IfExp, ast.While)):
                condition = ast.unparse(node.test).lower()
                if any(term in condition for term in category_terms):
                    category_branches += 1
                body = ast.unparse(node).lower()
                if "role" in condition and any(term in body for term in ("defer", "reject", "eligible", "admit", "no_memory")):
                    source_role_gates += 1
    reachable_legacy = sorted(seen & legacy)
    print(json.dumps({
        "reachable_modules": sorted(seen),
        "reachable_legacy_modules": reachable_legacy,
        "legacy_reachable_count": len(reachable_legacy),
        "content_category_branch_count": category_branches,
        "source_role_gate_count": source_role_gates,
    }, sort_keys=True))
    return 0 if not reachable_legacy and category_branches == 0 and source_role_gates == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
