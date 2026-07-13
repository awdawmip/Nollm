from __future__ import annotations

from pathlib import Path

from nollm_core import AtomHandle, BridgeSpec, CoreRuntime, GeometryAddress, RecallBudget

from .handle_store import FileHandleStore
from .placement_contract import AccessDecision
from .recall import AccessRecallRequest
from .runtime import AccessRuntime
from .statement import MemoryStatement
from .statement_store import FileStatementStore


_RECALL_BUDGET = RecallBudget(2, 12, 1, 1, 1, 16)
_ALLOWED_KERNELS = ("bridge", "coverage_down", "coverage_up", "lateral")


class AccessMemoryLoop:
    """Access-owned bounded placement and recall orchestration for a workspace."""

    def __init__(self, workspace: str | Path) -> None:
        if type(workspace) is str:
            if not workspace:
                raise ValueError("workspace is required")
            root = Path(workspace)
        elif isinstance(workspace, Path):
            root = workspace
        else:
            raise TypeError("workspace must be a string or Path")
        self._workspace = root.resolve()
        self._closed = False

    @property
    def workspace(self) -> Path:
        return self._workspace

    def close(self) -> None:
        self._closed = True

    def __enter__(self) -> "AccessMemoryLoop":
        self._require_open()
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def cursor_cells(self, raw_cells: object) -> list[dict[str, object]]:
        if type(raw_cells) is not list:
            raise TypeError("cursor cells must be a list")
        cells = tuple(GeometryAddress.from_mapping(item) for item in raw_cells)
        if len(cells) > 8 or len(set(cells)) != len(cells):
            raise ValueError("cursor cells must be unique and bounded")
        return [cell.to_mapping() for cell in cells]

    def local_context(self, cursor_cells: object, request_id: str) -> list[dict[str, object]]:
        cells = self._cells(cursor_cells)
        if not cells:
            return []
        with self._runtime() as access:
            result = access.recall(AccessRecallRequest(
                request_id,
                tuple(sorted(cells, key=lambda item: item.stable_key())),
                (),
                _ALLOWED_KERNELS,
                _RECALL_BUDGET,
            ))
        return [
            {
                "statement_id": item.statement_id,
                "content_utf8": item.evidence_utf8,
                "handle": item.handle.to_mapping(),
                "address": item.handle.geometry_address.to_mapping(),
                "fallback_error": item.fallback_error,
            }
            for item in result.items
            if item.evidence_utf8 is not None
        ]

    def apply_placement(self, statement: MemoryStatement, placement: object, request_id: str) -> dict[str, object]:
        if type(statement) is not MemoryStatement:
            raise TypeError("statement must be MemoryStatement")
        if type(request_id) is not str or not request_id:
            raise ValueError("request_id is required")
        decision = self._decision(placement, statement, request_id)
        if decision is None:
            return {"outcome": "defer", "statement_id": statement.statement_id, "core_write_count": 0}
        statement_store = FileStatementStore(self._workspace)
        existed_before = statement_store.exists(statement.statement_id)
        with self._runtime() as access:
            access.capture(statement)
            try:
                result = access.apply(decision)
            except Exception:
                if not existed_before:
                    statement_store.discard_new(statement)
                raise
        return {
            "outcome": "applied",
            "statement_id": statement.statement_id,
            "action": decision.action,
            "handle": result.to_mapping() if type(result) is AtomHandle else None,
            "core_write_count": 1 if decision.action in {"new", "move", "revision_current", "revision_keep_history", "stitch"} else 0,
        }

    def binding(self, statement_id: str) -> dict[str, object]:
        if type(statement_id) is not str or not statement_id:
            raise ValueError("statement_id is required")
        with self._runtime() as access:
            handle = access.saved_handle(statement_id)
            return access.handle_store.binding_for_handle(handle).to_mapping()

    def _decision(self, raw: object, statement: MemoryStatement, request_id: str) -> AccessDecision | None:
        if type(raw) is not dict or raw.get("schema_version") != "nollm_openclaw_placement_v1" or type(raw.get("outcome")) is not str:
            raise ValueError("invalid placement envelope")
        if raw["outcome"] == "defer":
            if set(raw) != {"schema_version", "outcome", "reason_text"} or type(raw["reason_text"]) is not str:
                raise ValueError("invalid deferred placement")
            return None
        if raw["outcome"] != "apply" or set(raw) != {"schema_version", "outcome", "decision"} or type(raw["decision"]) is not dict:
            raise ValueError("invalid placement outcome")
        value = raw["decision"]
        if value.get("statement_id") != statement.statement_id or type(value.get("action")) is not str or type(value.get("reason_text")) is not str:
            raise ValueError("decision does not bind the formed statement")
        action = value["action"]
        target = GeometryAddress.from_mapping(value["target_cell"]) if value.get("target_cell") is not None else None
        handle = AtomHandle.from_mapping(value["existing_handle"]) if value.get("existing_handle") is not None else None
        bridge = BridgeSpec.from_mapping(value["bridge_spec"]) if action in {"stitch", "unstitch"} else None
        return AccessDecision(
            f"placement:{request_id}:{statement.statement_id}", statement.statement_id, action,
            target, handle, bridge, value["reason_text"], "llm",
        )

    def _cells(self, raw_cells: object) -> tuple[GeometryAddress, ...]:
        return tuple(GeometryAddress.from_mapping(item) for item in self.cursor_cells(raw_cells))

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("AccessMemoryLoop is closed")

    def _runtime(self):
        self._require_open()
        core = CoreRuntime(self._workspace)
        try:
            access = AccessRuntime(core, FileStatementStore(self._workspace), FileHandleStore(self._workspace))
        except Exception:
            core.close()
            raise

        class _RuntimeContext:
            def __enter__(self_inner) -> AccessRuntime:
                return access

            def __exit__(self_inner, *_args: object) -> None:
                access.close()
                core.close()

        return _RuntimeContext()
