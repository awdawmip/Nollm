from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
from time import perf_counter
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(ROOT / "packages/nollm-core/src"),
    str(ROOT / "packages/nollm-access/src"),
    str(ROOT / "integrations/openclaw/formation-loop/python"),
]

from nollm_access import AccessDecision, AccessRuntime, FileHandleStore, FileStatementStore  # noqa: E402
from nollm_core import CoreRuntime  # noqa: E402
from nollm_openclaw_formation.memory_loop import (  # noqa: E402
    advance_placement_traversal,
    apply_placement,
    build_placement_prompt,
    build_revision_confirmation_prompt,
    build_revision_redecision_prompt,
    parse_revision_confirmation,
)


BX_STATEMENT_ID = "dream:91b6c843119549038dd2bbb0a40a8452f82edf5c158cac39c877c691f22280dc"
CR_STATEMENT_ID = "dream:82b8b33fc8c0cf13220db726e34f67fe781ddaa073d5033c7d739766e3e268d9"
BX_CONTENT = "Alpha项目 V3.9 发布校验码是 BX-3917。"
CR_CONTENT = "用户要求记忆：CAOLD广域余量验收的发布校验码是 CR-7159。"


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


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def inventory(workspace: Path) -> dict[str, object]:
    workspace = workspace.resolve()
    statements = FileStatementStore(workspace)
    handles = FileHandleStore(workspace)
    bx = statements.get(BX_STATEMENT_ID)
    cr = statements.get(CR_STATEMENT_ID)
    if bx.content_utf8 != BX_CONTENT or cr.content_utf8 != CR_CONTENT:
        raise ValueError("P1 repair source Statements do not match the accepted task identity")
    binding_document = json.loads(handles.state_bytes().decode("utf-8"))
    with CoreRuntime(workspace) as core:
        cells = core.occupied_cells()
        core_atoms = {
            handle: atom
            for address in cells
            for handle, atom in core.atoms_at(address)
        }
        bridge_count = len(core.bridges())
        atom_count = core.placement_count()
    bx_handle = handles.get(BX_STATEMENT_ID) if handles.exists(BX_STATEMENT_ID) else None
    cr_handle = handles.get(CR_STATEMENT_ID) if handles.exists(CR_STATEMENT_ID) else None
    bx_atom = core_atoms.get(bx_handle) if bx_handle is not None else None
    cr_atom = core_atoms.get(cr_handle) if cr_handle is not None else None
    return {
        "workspace": str(workspace),
        "workspace_tree_sha256": _tree_sha256(workspace),
        "statement_tree_sha256": _tree_sha256(workspace / "access" / "statements"),
        "statement_count": len(tuple((workspace / "access" / "statements").rglob("*.json"))),
        "binding_sha256": _sha(workspace / "access" / "bindings.json"),
        "binding_count": len(binding_document["bindings"]),
        "core_state_sha256": _sha(workspace / "core" / "current_state.json"),
        "occupied_cell_count": len(cells),
        "atom_count": atom_count,
        "bridge_count": bridge_count,
        "bx_statement_exists": True,
        "cr_statement_exists": True,
        "bx_handle": bx_handle.to_mapping() if bx_handle else None,
        "cr_handle": cr_handle.to_mapping() if cr_handle else None,
        "bx_atom_id": bx_atom.atom_id if bx_atom else None,
        "bx_payload_utf8": bx_atom.payload_utf8 if bx_atom else None,
        "cr_atom_id": cr_atom.atom_id if cr_atom else None,
        "cr_payload_utf8": cr_atom.payload_utf8 if cr_atom else None,
    }


def validate_and_optionally_restore(workspace: Path, apply_restore: bool = False) -> dict[str, object]:
    workspace = workspace.resolve()
    before = inventory(workspace)
    bx_bound = before["bx_handle"] is not None
    cr_bound = before["cr_handle"] is not None
    repair_required = not bx_bound and cr_bound
    already_restored = bx_bound and not cr_bound
    split_complete = bx_bound and cr_bound and before["bx_handle"] != before["cr_handle"]
    if not repair_required and not already_restored and not split_complete:
        raise ValueError("workspace is neither the accepted pre-repair state nor the restored state")

    action = "dry_run"
    if apply_restore and repair_required:
        handles = FileHandleStore(workspace)
        cr_handle = handles.get(CR_STATEMENT_ID)
        with CoreRuntime(workspace) as core:
            with AccessRuntime(core, FileStatementStore(workspace), handles) as access:
                access.apply(AccessDecision(
                    "p1-repair:restore-bx-current",
                    BX_STATEMENT_ID,
                    "revision_current",
                    existing_handle=cr_handle,
                    reason_text="task-authorized P1 repair restores the accepted BX current binding",
                    decided_by="human",
                ))
        action = "restored_bx_current"
    elif apply_restore and already_restored:
        action = "already_restored"
    elif apply_restore:
        action = "already_split"

    after = inventory(workspace)
    restored = after["bx_handle"] is not None and after["cr_handle"] is None
    checks = {
        "source_statements_preserved": (
            before["statement_tree_sha256"] == after["statement_tree_sha256"]
            and before["statement_count"] == after["statement_count"]
        ),
        "binding_count_preserved": before["binding_count"] == after["binding_count"],
        "atom_count_preserved": before["atom_count"] == after["atom_count"],
        "cell_count_preserved": before["occupied_cell_count"] == after["occupied_cell_count"],
        "bridge_count_preserved": before["bridge_count"] == after["bridge_count"],
        "dry_run_is_read_only": apply_restore or before["workspace_tree_sha256"] == after["workspace_tree_sha256"],
        "requested_state_reached": (restored or split_complete) if apply_restore else (repair_required or already_restored or split_complete),
    }
    return {
        "schema_version": "nollm_p1_dual_fact_repair_validation_v1",
        "mode": "apply_restore" if apply_restore else "dry_run",
        "action": action,
        "repair_required_before": repair_required,
        "already_restored_before": already_restored,
        "split_complete_before": split_complete,
        "before": before,
        "after": after,
        "checks": checks,
        "passed": all(checks.values()),
    }


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


def _host_json(prompt: str, session_id: str, timeout_seconds: int) -> tuple[str, int]:
    wrapper = shutil.which("openclaw") or shutil.which("openclaw.cmd")
    if wrapper is None:
        raise FileNotFoundError("openclaw executable is not available")
    root = Path(wrapper).parent
    started = perf_counter()
    result = subprocess.run(
        [
            str(root / "node.exe"), str(root / "node_modules/openclaw/openclaw.mjs"),
            "agent", "--agent", "nollm-dream-agent", "--session-id", session_id,
            "--message", prompt, "--model", "meituan/LongCat-2.0",
            "--timeout", str(timeout_seconds), "--json",
        ],
        check=False, capture_output=True, text=True, encoding="utf-8", errors="strict",
        timeout=timeout_seconds + 30,
    )
    elapsed_ms = int((perf_counter() - started) * 1000)
    if result.returncode != 0:
        raise RuntimeError(f"OpenClaw Host call failed ({result.returncode}): {result.stderr.strip()}")
    raw = _extract_text(json.loads(result.stdout)).strip()
    json.loads(raw)
    return raw, elapsed_ms


def place_existing_cr_with_real_host(workspace: Path, timeout_seconds: int = 240) -> dict[str, object]:
    workspace = workspace.resolve()
    before = inventory(workspace)
    if before["bx_handle"] is None or before["cr_handle"] is not None:
        raise ValueError("real CR Placement requires restored BX current and unbound CR Statement")
    statement = FileStatementStore(workspace).get(CR_STATEMENT_ID)
    request_id = f"p1-repair:place-cr:{uuid4().hex}"
    workspace_wire = str(workspace)
    built = build_placement_prompt(statement.to_mapping(), workspace_wire, request_id)
    surface_path = []
    host_calls = []
    traversal = 0
    while built.get("status") in {"traverse", "physical_entry"} and traversal < 32:
        surface_path.append(built.get("surface") or built.get("physical_entries"))
        raw, elapsed_ms = _host_json(built["prompt"], f"p1-cr-surface-{uuid4().hex}", timeout_seconds)
        host_calls.append({"stage": f"surface_{traversal}", "elapsed_ms": elapsed_ms, "response": json.loads(raw), "response_sha256": sha256(raw.encode("utf-8")).hexdigest()})
        built = advance_placement_traversal(statement.to_mapping(), built["traversal_state"], raw, workspace_wire)
        traversal += 1
    if built.get("status") != "placement_decision" or type(built.get("prompt")) is not str:
        after = inventory(workspace)
        checks = {
            "placement_applied": False,
            "traversal_deferred_without_write": built.get("status") == "defer" and before["workspace_tree_sha256"] == after["workspace_tree_sha256"],
        }
        return {
            "schema_version": "nollm_p1_real_host_cr_placement_v1",
            "provider": "meituan", "model": "LongCat-2.0",
            "request_id": request_id,
            "attempt": "traversal_defer",
            "traversal_result": built,
            "surface_path": surface_path,
            "host_calls": host_calls,
            "before": before,
            "after": after,
            "checks": checks,
            "passed": False,
        }

    placement_raw, elapsed_ms = _host_json(built["prompt"], f"p1-cr-placement-{uuid4().hex}", timeout_seconds)
    host_calls.append({"stage": "placement", "elapsed_ms": elapsed_ms, "response": json.loads(placement_raw), "response_sha256": sha256(placement_raw.encode("utf-8")).hexdigest()})
    applied = apply_placement(placement_raw, statement.to_mapping(), workspace_wire, request_id, built.get("selected_entry"))
    attempt = "initial"
    confirmation_outcome = None
    if applied.get("outcome") == "revision_confirmation_required":
        provisional = applied["provisional_revision"]
        confirmation_prompt = build_revision_confirmation_prompt(provisional)["prompt"]
        confirmation_raw, elapsed_ms = _host_json(confirmation_prompt, f"p1-cr-confirm-{uuid4().hex}", timeout_seconds)
        host_calls.append({"stage": "revision_confirmation", "elapsed_ms": elapsed_ms, "response": json.loads(confirmation_raw), "response_sha256": sha256(confirmation_raw.encode("utf-8")).hexdigest()})
        confirmation = parse_revision_confirmation(confirmation_raw, provisional)["confirmation"]
        confirmation_outcome = confirmation["outcome"]
        if confirmation_outcome == "confirm_revision":
            applied = apply_placement(placement_raw, statement.to_mapping(), workspace_wire, request_id, built.get("selected_entry"), confirmation)
            attempt = "confirmed_revision"
        elif confirmation_outcome == "reject_revision":
            redecision = build_revision_redecision_prompt(built["prompt"], provisional, confirmation)
            redecision_raw, elapsed_ms = _host_json(redecision["prompt"], f"p1-cr-redecision-{uuid4().hex}", timeout_seconds)
            host_calls.append({"stage": "revision_redecision", "elapsed_ms": elapsed_ms, "response": json.loads(redecision_raw), "response_sha256": sha256(redecision_raw.encode("utf-8")).hexdigest()})
            applied = apply_placement(
                redecision_raw, statement.to_mapping(), workspace_wire, request_id,
                built.get("selected_entry"), None, redecision["excluded_revision_targets"],
            )
            attempt = "revision_redecision"

    after = inventory(workspace)
    checks = {
        "placement_applied": applied.get("outcome") == "applied",
        "cr_action_is_nondestructive": applied.get("action") in {"new_local", "expand_surface"},
        "bx_and_cr_have_distinct_handles": after["bx_handle"] is not None and after["cr_handle"] is not None and after["bx_handle"] != after["cr_handle"],
        "bx_payload_preserved": after["bx_payload_utf8"] == BX_CONTENT,
        "cr_payload_current": after["cr_payload_utf8"] == CR_CONTENT,
        "statement_tree_preserved": before["statement_tree_sha256"] == after["statement_tree_sha256"],
        "one_binding_added": after["binding_count"] == before["binding_count"] + 1,
        "one_atom_added": after["atom_count"] == before["atom_count"] + 1,
    }
    return {
        "schema_version": "nollm_p1_real_host_cr_placement_v1",
        "provider": "meituan", "model": "LongCat-2.0",
        "request_id": request_id,
        "attempt": attempt,
        "confirmation_outcome": confirmation_outcome,
        "placement_result": applied,
        "surface_path": surface_path,
        "host_calls": host_calls,
        "before": before,
        "after": after,
        "checks": checks,
        "passed": all(checks.values()),
    }


def replay_real_host_receipt(workspace: Path, receipt_path: Path) -> dict[str, object]:
    workspace = workspace.resolve()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema_version") != "nollm_p1_real_host_cr_placement_v1" or receipt.get("passed") is not True:
        raise ValueError("source receipt is not a passed real Host CR Placement")
    before = inventory(workspace)
    if before["bx_handle"] is None or before["cr_handle"] is not None:
        raise ValueError("receipt replay requires restored BX current and unbound CR Statement")
    statement = FileStatementStore(workspace).get(CR_STATEMENT_ID)
    workspace_wire = str(workspace)
    request_id = receipt["request_id"]
    built = build_placement_prompt(statement.to_mapping(), workspace_wire, request_id)
    replayed_stages = []
    placement_response = None
    for call in receipt["host_calls"]:
        raw = json.dumps(call["response"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if call["stage"].startswith("surface_"):
            if built.get("status") not in {"traverse", "physical_entry"}:
                raise ValueError("receipt has an unexpected Surface response")
            built = advance_placement_traversal(statement.to_mapping(), built["traversal_state"], raw, workspace_wire)
            replayed_stages.append(call["stage"])
        elif call["stage"] == "placement":
            placement_response = raw
            replayed_stages.append("placement")
    if built.get("status") != "placement_decision" or placement_response is None:
        raise ValueError("receipt replay did not reach an exact Placement decision")
    applied = apply_placement(
        placement_response, statement.to_mapping(), workspace_wire,
        request_id, built.get("selected_entry"),
    )
    after = inventory(workspace)
    checks = {
        "source_receipt_passed": True,
        "exact_stages_replayed": replayed_stages == [call["stage"] for call in receipt["host_calls"]],
        "placement_applied": applied.get("outcome") == "applied",
        "same_action": applied.get("action") == receipt["placement_result"]["action"] == "new_local",
        "same_cr_handle": applied.get("handle") == receipt["after"]["cr_handle"],
        "bx_and_cr_distinct": after["bx_handle"] != after["cr_handle"],
        "statement_tree_preserved": before["statement_tree_sha256"] == after["statement_tree_sha256"],
        "one_binding_added": after["binding_count"] == before["binding_count"] + 1,
        "one_atom_added": after["atom_count"] == before["atom_count"] + 1,
    }
    return {
        "schema_version": "nollm_p1_real_host_cr_placement_replay_v1",
        "source_receipt": str(receipt_path.resolve()),
        "source_request_id": request_id,
        "replayed_stages": replayed_stages,
        "placement_result": applied,
        "before": before,
        "after": after,
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply-restore", action="store_true")
    parser.add_argument("--place-cr-real", action="store_true")
    parser.add_argument("--replay-real-receipt", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=240)
    args = parser.parse_args()
    if sum((args.apply_restore, args.place_cr_real, args.replay_real_receipt is not None)) > 1:
        parser.error("choose only one mutation mode")
    result = (
        place_existing_cr_with_real_host(args.workspace, args.timeout_seconds)
        if args.place_cr_real else (
            replay_real_host_receipt(args.workspace, args.replay_real_receipt)
            if args.replay_real_receipt is not None
            else validate_and_optionally_restore(args.workspace, args.apply_restore)
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
