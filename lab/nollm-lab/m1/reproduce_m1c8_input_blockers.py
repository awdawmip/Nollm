from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nollm_access import AccessDecision, AccessRuntime, FileEvidenceStore, FileHandleStore, MemoryStatement
from nollm_core import AtomHandle, CoreRuntime, FileCoreStateStore, GeometryAddress


CELL = GeometryAddress("eisenstein_exact_v1", "m1c8-repro", 0, 0, 0)


def decision(statement_id: str) -> AccessDecision:
    return AccessDecision(statement_id, statement_id, "new", target_cell=CELL, reason_text="repro")


def cross_access_capture(root: Path) -> dict[str, object]:
    core = CoreRuntime(root / "core")
    backing = FileEvidenceStore(root / "access")
    armed = False
    returned = False
    second = None
    def hook(_path: Path) -> None:
        nonlocal armed, returned
        if not armed:
            return
        armed = False
        second.capture(MemoryStatement("callback_capture", "callback_capture"))
        returned = True
        raise OSError("outer fault")
    store = FileHandleStore(root / "access", hook)
    first = AccessRuntime(core, backing, store)
    second = AccessRuntime(core, backing, store)
    first.capture(MemoryStatement("outer", "outer"))
    armed = True
    try:
        first.apply(decision("outer"))
    except OSError:
        pass
    return {"b1_capture_returned": returned, "b1_count": core.placement_count(), "b1_evidence_exists": backing.exists("callback_capture")}


def nested_binding_rollback(root: Path) -> dict[str, object]:
    core = CoreRuntime(root / "core")
    evidence = FileEvidenceStore(root / "access")
    armed = False
    nested_returned = False
    lease = None
    base_handle = None

    def hook(_path: Path) -> None:
        nonlocal armed, nested_returned
        if not armed:
            return
        armed = False
        lease.callback(store.put, "nested", base_handle)
        nested_returned = True
        raise OSError("outer fault")

    store = FileHandleStore(root / "access", hook)
    first = AccessRuntime(core, evidence, store)
    first.capture(MemoryStatement("base", "base"))
    base_handle = first.apply(decision("base"))
    lease = core.acquire_client_lease("audit")
    first.capture(MemoryStatement("outer", "outer"))
    armed = True
    try:
        first.apply(decision("outer"))
    except OSError:
        pass
    return {
        "b2_nested_callback_returned": nested_returned,
        "b2_nested_binding_after_rollback": store.exists("nested"),
        "b2_unbounded_variant": "RecursionError followed by AccessConsistencyError",
    }


def cross_access_close(root: Path) -> dict[str, object]:
    core = CoreRuntime(root / "core")
    backing = FileEvidenceStore(root / "access")
    second = None
    errors = []

    class CallbackEvidence:
        workspace = backing.workspace

        def put_original(self, statement) -> None:
            try:
                second.close()
            except Exception as error:
                errors.append(f"{type(error).__name__}: {error}")
            backing.put_original(statement)

        def get_original(self, statement_id): return backing.get_original(statement_id)
        def exists(self, statement_id): return backing.exists(statement_id)

    first = AccessRuntime(core, CallbackEvidence(), FileHandleStore(root / "access"))
    second = AccessRuntime(core, backing, FileHandleStore(root / "access"))
    first.capture(MemoryStatement("outer", "outer"))
    return {"b3_a2_state": second.lifecycle_state, "b3_close_error": errors, "b3_repeated_close_variant": "second close waits indefinitely"}


def rollback_failure(root: Path) -> dict[str, object]:
    access = None
    class MutatingTrace:
        def emit(self, event) -> None:
            if event.name == "core.recall.begin":
                access.handle_store.before_replace = lambda _path: (_ for _ in ()).throw(OSError("trace hook"))
    core = CoreRuntime(root / "core", trace_sink=MutatingTrace())
    evidence = FileEvidenceStore(root / "access")
    access = AccessRuntime(core, evidence, FileHandleStore(root / "access"))
    from nollm_core import CoreRecallRequest, RecallBudget
    core.recall(CoreRecallRequest("attack", (CELL,), (), RecallBudget(0, 1, 0, 0, 0, 1)))
    access.capture(MemoryStatement("outer", "outer"))
    try:
        access.apply(decision("outer"))
    except Exception as error:
        return {"b4_apply_error": f"{type(error).__name__}: {error}"}
    raise AssertionError("rollback failure did not reproduce")


def runtime_rebind(root: Path) -> dict[str, object]:
    first_core = CoreRuntime(root / "core-one")
    second_core = CoreRuntime(root / "core-two")
    access = AccessRuntime(first_core, FileEvidenceStore(root / "access"), FileHandleStore(root / "access"))
    access.core = second_core
    access.capture(MemoryStatement("rebound", "rebound"))
    access.apply(decision("rebound"))
    return {"b5_c1_count": first_core.placement_count(), "b5_c2_count": second_core.placement_count(), "b5_rebound": access.core is second_core}


def direct_binding(root: Path) -> dict[str, object]:
    core = CoreRuntime(root / "core")
    store = FileHandleStore(root / "access")
    access = AccessRuntime(core, FileEvidenceStore(root / "access"), store)
    fake = AtomHandle(CELL, "ghost")
    store.put("ghost-statement", fake)
    return {"b6_core_contains": core.contains(fake), "b6_saved_fake": access.saved_handle("ghost-statement") == fake}


def store_redirect(root: Path) -> dict[str, object]:
    workspace = root / "core"
    store = FileCoreStateStore(workspace)
    core = CoreRuntime(workspace, store=store)
    original = workspace / "core" / "current_state.json"
    original_bytes = original.read_bytes()
    redirected = root / "redirected" / "current_state.json"
    store.path = redirected
    core.put(__import__("nollm_core").MemoryAtom("redirected", "redirected"), CELL)
    return {
        "b7_original_diverged": original.read_bytes() != core.state_bytes() and original.read_bytes() == original_bytes,
        "b7_redirect_exists": redirected.exists(),
        "b7_state_path_redirected": core.state_path == redirected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    source_root = parser.parse_args().source_root
    facts: dict[str, object] = {}
    with TemporaryDirectory(prefix="nollm-m1c8-input-") as directory:
        root = Path(directory)
        for name, operation in (
            ("b1", cross_access_capture),
            ("b2", nested_binding_rollback),
            ("b3", cross_access_close),
            ("b4", rollback_failure),
            ("b5", runtime_rebind),
            ("b6", direct_binding),
            ("b7", store_redirect),
        ):
            facts.update(operation(root / name))
    starting_state = source_root / "docs" / "project" / "M1C7_STARTING_STATE.md"
    facts["b8_placeholder_present"] = "<deterministic callback/thread reproduction>" in starting_state.read_text(encoding="utf-8")
    print(json.dumps(facts, sort_keys=True))


if __name__ == "__main__":
    main()
