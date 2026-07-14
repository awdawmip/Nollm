from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "packages/nollm-core/src"), str(ROOT / "packages/nollm-access/src")]

from nollm_access import AccessDecision, AccessRuntime, FileHandleStore, FileStatementStore, MemoryStatement  # noqa: E402
from nollm_core import CoreRuntime, GeometryAddress, expand_physical_coverage  # noqa: E402


SOURCE_ID = "v38:cross-layer-entry"
TARGET_ID = "v38:cross-layer-target"


def seed(workspace: Path) -> dict[str, object]:
    source = GeometryAddress("default_dream_v1", "default", 0, -12, 9)
    expansion = expand_physical_coverage(source, "coverage_down")
    target = max(expansion.members, key=lambda member: (member.weight_q16, member.target.stable_key())).target
    with CoreRuntime(workspace) as core:
        with AccessRuntime(core, FileStatementStore(workspace), FileHandleStore(workspace)) as access:
            for statement_id, content, address in (
                (SOURCE_ID, "V3.8跨层验证入口：蓝杉协议的实际保管代码只记录在相邻物理层。", source),
                (TARGET_ID, "蓝杉协议的保管代码是 TC-3817；该代码来自相邻物理层记录。", target),
            ):
                access.capture(MemoryStatement(statement_id, content))
                access.apply(AccessDecision(f"decision:{statement_id}", statement_id, "new", target_cell=address, reason_text="controlled V3.8 live fixture", decided_by="fixture"))
        placement_count = core.placement_count()
    return {
        "schema_version": "nollm_translation_covariant_live_fixture_v1",
        "source_statement_id": SOURCE_ID,
        "target_statement_id": TARGET_ID,
        "source_address": source.to_mapping(),
        "target_address": target.to_mapping(),
        "required_path": ["coverage_down"],
        "placement_count_after": placement_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    document = seed(arguments.workspace)
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        arguments.output.write_text(payload, encoding="utf-8", newline="\n")
    print(json.dumps(document, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
