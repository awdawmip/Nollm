from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from time import perf_counter
from uuid import uuid4


CASES = (
    {
        "case_id": "C1",
        "old": "Alpha发布负责人是Priya。",
        "new": "Alpha发布负责人是Priya。",
        "allowed": ("reuse",),
        "forbidden": ("revision_current", "new_local", "expand_surface"),
    },
    {
        "case_id": "C2",
        "old": "Alpha发布校验码是 BX-3917。",
        "new": "Alpha发布校验码已更新为 BX-4021。",
        "allowed": ("revision_current",),
        "forbidden": ("reuse", "new_local", "expand_surface"),
    },
    {
        "case_id": "C3",
        "old": "Alpha项目 V3.9 发布校验码是 BX-3917。",
        "new": "CAOLD广域余量验收发布校验码是 CR-7159。",
        "allowed": ("new_local", "expand_surface", "defer"),
        "forbidden": ("revision_current", "reuse"),
    },
    {
        "case_id": "C4",
        "old": "Alpha发布校验码是 BX-3917。",
        "new": "Alpha回滚负责人是Ken。",
        "allowed": ("new_local",),
        "forbidden": ("revision_current", "reuse"),
    },
    {
        "case_id": "C5",
        "old": "Alpha发布校验码是 BX-3917。",
        "new": "发布校验码改成 CX-1。（未说明主体）",
        "allowed": ("defer",),
        "forbidden": ("revision_current", "reuse"),
    },
)


def _tree_sha256(root: Path) -> str:
    digest = sha256()
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _extract_text(value: object) -> str:
    if type(value) is dict:
        if type(value.get("text")) is str:
            return value["text"]
        for key in ("payloads", "result", "payload", "message"):
            if key in value:
                found = _extract_text(value[key])
                if found:
                    return found
    if type(value) is list:
        for item in value:
            found = _extract_text(item)
            if found:
                return found
    return ""


def _call_host(prompt: str, session_id: str, timeout_seconds: int) -> tuple[dict[str, object], int]:
    started = perf_counter()
    wrapper = shutil.which("openclaw") or shutil.which("openclaw.cmd")
    if wrapper is None:
        raise FileNotFoundError("openclaw executable is not available")
    wrapper_path = Path(wrapper)
    node = wrapper_path.with_name("node.exe")
    cli = wrapper_path.parent / "node_modules" / "openclaw" / "openclaw.mjs"
    if not node.is_file() or not cli.is_file():
        raise FileNotFoundError("OpenClaw Node launcher is incomplete")
    result = subprocess.run(
        [
            str(node), str(cli), "agent", "--agent", "nollm-dream-agent",
            "--session-id", session_id, "--message", prompt,
            "--model", "meituan/LongCat-2.0", "--timeout", str(timeout_seconds), "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=timeout_seconds + 30,
    )
    elapsed_ms = int((perf_counter() - started) * 1000)
    if result.returncode != 0:
        raise RuntimeError(f"OpenClaw Host call failed ({result.returncode}): {result.stderr.strip()}")
    envelope = json.loads(result.stdout)
    text = _extract_text(envelope).strip()
    return json.loads(text), elapsed_ms


def _placement_prompt(case: dict[str, object]) -> str:
    candidate = {
        "candidate_id": "existing:0",
        "existing_handle": {
            "geometry_address": {
                "profile_id": "default_dream_v1", "chart_id": "default",
                "layer": 0, "q": 0, "r": 0, "phase": None,
            },
            "current_statement": case["old"],
        },
    }
    return f"""You are a private no-write semantic placement evaluator. Do not call tools or reveal reasoning.
Choose exactly one action from reuse, revision_current, new_local, expand_surface, defer.
reuse: materially the same current fact.
revision_current: only the same subject or referent, same proposition slot, and a new value that explicitly supersedes the current value. Similar wording, analogous fields on different subjects, or an additive fact is not revision.
new_local: a distinct fact suitable near the supplied candidate.
expand_surface: a distinct fact requiring a new locality.
defer: identity, supersession, or placement is uncertain.
Return exactly one raw JSON object: {{"schema_version":"nollm_semantic_revision_contrast_v1","action":"one action"}}
old_statement: {json.dumps(case["old"], ensure_ascii=False)}
new_statement: {json.dumps(case["new"], ensure_ascii=False)}
finite_candidates: {json.dumps([candidate], ensure_ascii=False, sort_keys=True, separators=(",", ":"))}"""


def _confirmation_prompt(case: dict[str, object]) -> str:
    return f"""You are a private no-write destructive-revision confirmation evaluator. Do not call tools or reveal reasoning.
Confirm only if the Statements have the same subject or referent, the same proposition slot, and the new value explicitly supersedes the current value.
Return exactly one raw JSON object with only schema_version, outcome, relation.
confirm: {{"schema_version":"nollm_openclaw_revision_confirmation_v1","outcome":"confirm_revision","relation":"same_subject_same_slot_supersedes"}}
reject: {{"schema_version":"nollm_openclaw_revision_confirmation_v1","outcome":"reject_revision","relation":"different_subject_or_non_superseding"}}
defer: {{"schema_version":"nollm_openclaw_revision_confirmation_v1","outcome":"defer","relation":"uncertain"}}
current_statement: {json.dumps(case["old"], ensure_ascii=False)}
proposed_statement: {json.dumps(case["new"], ensure_ascii=False)}"""


def run(workspace: Path, timeout_seconds: int = 240) -> dict[str, object]:
    workspace = workspace.resolve()
    before = _tree_sha256(workspace)
    outcomes = []
    run_id = uuid4().hex
    for case in CASES:
        placement, placement_ms = _call_host(
            _placement_prompt(case), f"semantic-contrast-{run_id}-{case['case_id'].lower()}", timeout_seconds,
        )
        if set(placement) != {"schema_version", "action"} or placement.get("schema_version") != "nollm_semantic_revision_contrast_v1":
            raise ValueError(f"{case['case_id']} returned an invalid placement envelope")
        action = placement["action"]
        confirmation = None
        confirmation_ms = 0
        if case["case_id"] == "C2" and action == "revision_current":
            confirmation, confirmation_ms = _call_host(
                _confirmation_prompt(case), f"semantic-confirm-{run_id}-c2", timeout_seconds,
            )
            if set(confirmation) != {"schema_version", "outcome", "relation"}:
                raise ValueError("C2 returned an invalid confirmation envelope")
        passed = action in case["allowed"]
        if case["case_id"] == "C2":
            passed = passed and confirmation == {
                "schema_version": "nollm_openclaw_revision_confirmation_v1",
                "outcome": "confirm_revision",
                "relation": "same_subject_same_slot_supersedes",
            }
        outcomes.append({
            "case_id": case["case_id"],
            "old_sha256": sha256(case["old"].encode("utf-8")).hexdigest(),
            "new_sha256": sha256(case["new"].encode("utf-8")).hexdigest(),
            "allowed_actions": list(case["allowed"]),
            "forbidden_actions": list(case["forbidden"]),
            "action": action,
            "confirmation": confirmation,
            "placement_ms": placement_ms,
            "confirmation_ms": confirmation_ms,
            "passed": passed,
        })
    after = _tree_sha256(workspace)
    checks = {
        "all_cases_passed": all(item["passed"] for item in outcomes),
        "c3_c4_never_revision": all(item["action"] != "revision_current" for item in outcomes if item["case_id"] in {"C3", "C4"}),
        "sandbox_zero_write": before == after,
    }
    return {
        "schema_version": "nollm_real_host_revision_semantic_contrast_v1",
        "provider": "meituan",
        "model": "LongCat-2.0",
        "workspace": str(workspace),
        "workspace_tree_sha256_before": before,
        "workspace_tree_sha256_after": after,
        "outcomes": outcomes,
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=240)
    args = parser.parse_args()
    result = run(args.workspace, args.timeout_seconds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
