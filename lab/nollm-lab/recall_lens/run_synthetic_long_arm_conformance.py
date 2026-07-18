from __future__ import annotations

import json
from pathlib import Path
import tempfile

from nollm_access import AccessMemoryLoop
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom
from nollm_openclaw_formation.sculptor import apply_dream_sculptor_result, build_dream_sculptor_prompt


FACTS = (
    ("target", "2026年7月17日东京下雨。"),
    ("tokyo-1", "用户在东京取消了浅草行程。"),
    ("tokyo-2", "用户随后从浅草改去东京站。"),
    ("date-1", "2026年7月17日用户参加线上会议。"),
    ("date-2", "2026年7月17日晚上用户提交了会议记录。"),
    ("weather-1", "大阪在2026年7月17日也下雨。"),
    ("weather-2", "大阪傍晚的降雨已经停止。"),
    ("unrelated-1", "实验室更换了显微镜灯泡。"),
    ("unrelated-2", "显微镜随后完成了校准。"),
)


def _wire(index: int, capture: dict[str, object], atlas: dict[str, object], candidate_id: str) -> str:
    quote = capture["user_utf8"]
    assert isinstance(quote, str)
    path = next(item for item in atlas["paths"] if candidate_id in item["leaf_locality_candidate_ids"])
    plan = {
        "draft_id": "d1",
        "content_utf8": FACTS[index][1],
        "source_capture_ids": [capture["capture_id"]],
        "lenses": [{
            "lens_id": "lens-synthetic-arm",
            "future_query": "Which bounded locality should this complete fact grow from?",
            "basis_spans": [{"capture_id": capture["capture_id"], "role": "user", "start": 0, "end": len(quote), "quote_utf8": quote}],
            "atlas_path_ids": [path["path_id"]],
            "leaf_locality_candidate_ids": [candidate_id],
            "unresolved": False,
        }],
        "action": "new_local",
        "existing_handle": None,
        "reason_text": "synthetic long-arm contract fixture",
    }
    return json.dumps({"schema_version": "nollm_openclaw_dream_sculptor_v2", "outcome": "plan", "plans": [plan], "defer_reason": None}, ensure_ascii=False)


def _candidate_for_statement(atlas: dict[str, object], statement_id: str) -> dict[str, object]:
    return next(item for item in atlas["candidates"] if any(statement.get("statement_id") == statement_id for statement in item["representative_statements"]))


def validate(workspace: str | Path | None = None) -> dict[str, object]:
    owned = workspace is None
    root = Path(tempfile.mkdtemp(prefix="nollm-caold-synthetic-long-arm-")) if owned else Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    outcomes = []
    statement_ids = {}
    try:
        unrelated_seed = GeometryAddress("default_dream_v1", "default", 0, 20, -20)
        target_seed = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
        with CoreRuntime(root) as core:
            core.put(MemoryAtom("lab-target-seed", "Lab-only target geometry control"), target_seed)
            core.put(MemoryAtom("lab-unrelated-seed", "Lab-only unrelated geometry control"), unrelated_seed)
        anchors = {0: None, 1: "target", 2: "tokyo-1", 3: "target", 4: "date-1", 5: "target", 6: "weather-1", 7: "lab-seed", 8: "unrelated-1"}
        for index, (name, content) in enumerate(FACTS):
            capture = {"capture_id": f"capture-{name}", "user_utf8": content, "assistant_utf8": "Acknowledged.", "captured_epoch_ms": 1_768_582_400_000 + index, "timezone_offset_minutes": 480}
            request_id = f"synthetic-arm-{name}"
            built = build_dream_sculptor_prompt([capture], str(root), request_id)
            anchor = anchors[index]
            if anchor is None:
                selected = next(item for item in built["atlas"]["candidates"] if target_seed.to_mapping() in item["geometry_addresses"])
            elif anchor == "lab-seed":
                selected = next(item for item in built["atlas"]["candidates"] if unrelated_seed.to_mapping() in item["geometry_addresses"])
            else:
                selected = _candidate_for_statement(built["atlas"], statement_ids[anchor])
            applied = apply_dream_sculptor_result(_wire(index, capture, built["atlas"], selected["candidate_id"]), [capture], built["atlas"], str(root), request_id)
            outcome = applied["outcomes"][0]
            if outcome["outcome"] != "applied":
                raise AssertionError(f"{name} was not applied: {outcome}")
            outcomes.append(outcome)
            statement_ids[name] = outcome["statement_id"]

        directions = {"tokyo": "tokyo-2", "absolute_time": "date-2", "weather": "weather-2"}
        recalls = {}
        for direction, name in directions.items():
            outcome = next(item for item in outcomes if item["statement_id"] == statement_ids[name])
            entry = GeometryAddress.from_mapping(outcome["junction"]["cell"])
            with AccessMemoryLoop(root) as loop:
                items = loop.local_context([entry.to_mapping()], f"recall-{direction}")
            target = next(item for item in items if item["statement_id"] == statement_ids["target"])
            recalls[direction] = {"entry": entry.to_mapping(), "target_handle": target["handle"], "path": target["path"], "entry_count": 1}
        unrelated_outcome = next(item for item in outcomes if item["statement_id"] == statement_ids["unrelated-2"])
        unrelated_entry = GeometryAddress.from_mapping(unrelated_outcome["junction"]["cell"])
        with AccessMemoryLoop(root) as loop:
            unrelated_items = loop.local_context([unrelated_entry.to_mapping()], "recall-unrelated")
        target_handles = {json.dumps(item["target_handle"], sort_keys=True) for item in recalls.values()}
        target_in_unrelated = any(item["statement_id"] == statement_ids["target"] for item in unrelated_items)
        durable = "\n".join(path.read_text("utf-8") for path in root.rglob("*.json"))
        result = {
            "schema_version": "nollm_lab_synthetic_long_arm_conformance_v2",
            "statement_count": len(outcomes),
            "target_statement_id": statement_ids["target"],
            "arm_lengths": {"tokyo": 2, "absolute_time": 2, "weather": 2, "unrelated": 2},
            "recalls": recalls,
            "independent_single_entry_count": len(recalls),
            "same_target_handle": len(target_handles) == 1,
            "unrelated_target_reached": target_in_unrelated,
            "persistent_lens_text_found": "lens-synthetic-arm" in durable or "future_query" in durable,
            "provider_backed": False,
            "lab_only_unrelated_seed": unrelated_seed.to_mapping(),
            "lab_only_target_seed": target_seed.to_mapping(),
        }
        result["passed"] = len(recalls) == 3 and len(target_handles) == 1 and all(len(item["path"]) >= 2 for item in recalls.values()) and not target_in_unrelated and not result["persistent_lens_text_found"]
        return result
    finally:
        if owned:
            import shutil
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True, indent=2))
