from __future__ import annotations

import json
from pathlib import Path
import tempfile

from nollm_access import AccessMemoryLoop
from nollm_core import GeometryAddress
from nollm_openclaw_formation.sculptor import apply_dream_sculptor_result, build_dream_sculptor_prompt


FACTS = (
    ("今天东京下雨了。", "2026年7月17日东京下雨了。"),
    ("我今天取消了浅草行程。", "2026年7月17日用户在东京取消了浅草行程。"),
    ("今天我参加了线上会议。", "2026年7月17日用户参加了线上会议。"),
    ("大阪今天也下雨了。", "2026年7月17日大阪也下雨了。"),
    ("东京站今天临时关闭了一个入口。", "2026年7月17日东京站临时关闭了一个入口。"),
    ("傍晚的降雨比中午更大。", "2026年7月17日傍晚的降雨比中午更大。"),
)


def _wire(index: int, capture: dict[str, object], candidate_id: str) -> str:
    quote = capture["user_utf8"]
    assert isinstance(quote, str)
    plan = {
        "draft_id": "d1",
        "content_utf8": FACTS[index][1],
        "source_capture_ids": [capture["capture_id"]],
        "lenses": [{
            "lens_id": "lens-observation",
            "future_query": "What related observation should this locality recall?",
            "basis_spans": [{
                "capture_id": capture["capture_id"], "role": "user",
                "start": 0, "end": len(quote), "quote_utf8": quote,
            }],
            "locality_candidate_ids": [candidate_id],
            "unresolved": False,
        }],
        "action": "expand_surface" if index == 0 else "new_local",
        "primary_candidate_id": candidate_id,
        "contact_candidate_ids": [],
        "existing_handle": None,
        "reason_text": "Tokyo/date/weather Observation fixture",
    }
    return json.dumps({
        "schema_version": "nollm_openclaw_dream_sculptor_v1",
        "outcome": "plan", "plans": [plan], "defer_reason": None,
    }, ensure_ascii=False)


def validate(workspace: str | Path | None = None) -> dict[str, object]:
    owned = workspace is None
    root = Path(tempfile.mkdtemp(prefix="nollm-caold-tokyo-")) if owned else Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    outcomes = []
    target_statement_id = None
    try:
        for index, (natural, _absolute) in enumerate(FACTS):
            capture = {
                "capture_id": f"capture-t{index}",
                "user_utf8": natural,
                "assistant_utf8": "知道了。",
                "captured_epoch_ms": 1_768_582_400_000 + index,
                "timezone_offset_minutes": 480,
            }
            request_id = f"tokyo-t{index}"
            built = build_dream_sculptor_prompt([capture], str(root), request_id)
            candidates = built["atlas"]["candidates"]
            if index == 0:
                selected = candidates[0]
            else:
                selected = next(
                    item for item in candidates
                    if any(statement["statement_id"] == target_statement_id for statement in item["representative_statements"])
                )
            applied = apply_dream_sculptor_result(
                _wire(index, capture, selected["candidate_id"]), [capture], built["atlas"], str(root), request_id,
            )
            outcome = applied["outcomes"][0]
            if outcome["outcome"] != "applied":
                raise AssertionError(f"T{index} was not applied: {outcome}")
            outcomes.append(outcome)
            if index == 0:
                target_statement_id = outcome["statement_id"]

        directions = {"tokyo": 1, "absolute_time": 2, "weather": 3}
        recalls = {}
        for direction, index in directions.items():
            entry = GeometryAddress.from_mapping(outcomes[index]["junction"]["cell"])
            with AccessMemoryLoop(root) as loop:
                items = loop.local_context([entry.to_mapping()], f"recall-{direction}")
            target = next(item for item in items if item["statement_id"] == target_statement_id)
            recalls[direction] = {
                "entry": entry.to_mapping(),
                "target_statement_id": target_statement_id,
                "target_handle": target["handle"],
                "path": target["path"],
                "entry_count": 1,
            }
        unrelated = GeometryAddress("default_dream_v1", "default", 0, 100, -100)
        with AccessMemoryLoop(root) as loop:
            none_items = loop.local_context([unrelated.to_mapping()], "recall-none")
        durable = "\n".join(path.read_text("utf-8") for path in root.rglob("*.json"))
        target_handles = {json.dumps(item["target_handle"], sort_keys=True) for item in recalls.values()}
        return {
            "schema_version": "nollm_lab_tokyo_time_weather_observation_v1",
            "workspace_name": "nollm-caold-recall-lens-junction-growth-v1",
            "statement_count": len(outcomes),
            "target_statement_id": target_statement_id,
            "target_atom_count": 1,
            "recalls": recalls,
            "independent_single_entry_count": len(recalls),
            "same_target_handle": len(target_handles) == 1,
            "none_result_count": len(none_items),
            "persistent_lens_text_found": "lens-observation" in durable or "future_query" in durable,
            "provider_backed": False,
            "gateway_restarted": False,
            "passed_deterministic_observation": (
                len(recalls) == 3 and len(target_handles) == 1
                and all(item["path"] == ["lateral"] for item in recalls.values())
                and not none_items and "lens-observation" not in durable and "future_query" not in durable
            ),
        }
    finally:
        if owned:
            import shutil
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True, indent=2))
