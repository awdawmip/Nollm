"""Explicit Host reorganization plans, independent of files and semantic routing."""
from __future__ import annotations

from dataclasses import dataclass

from nollm_core import (
    AtomHandle, GeometryAddress, MemoryAtom, MoveCommand, PutCommand,
    RemoveCommand, ReplaceCommand,
)

from .handle_store import HandleBinding
from .placement_contract import AccessDecision
from .statement import MemoryStatement


REORGANIZATION_ACTIONS = frozenset({
    "new", "reuse", "revision_current", "revision_keep_history", "move", "forget",
})


def handle_key(handle: AtomHandle):
    return handle.geometry_address.stable_key(), handle.local_atom_id


def reorganization_handles(decisions: tuple[AccessDecision, ...]) -> tuple[AtomHandle, ...]:
    """Include old and final handles, including destinations that are empty now."""
    handles = set()
    for decision in decisions:
        if not isinstance(decision, AccessDecision):
            raise TypeError("reorganization decisions must be AccessDecision values")
        if decision.action not in REORGANIZATION_ACTIONS:
            raise ValueError(f"unsupported reorganization action: {decision.action}")
        if decision.existing_handle is not None:
            handles.add(decision.existing_handle)
        if decision.action in {"new", "revision_keep_history"}:
            handles.add(AtomHandle(decision.target_cell, decision.statement_id))
        elif decision.action == "move":
            handles.add(AtomHandle(decision.target_cell, decision.existing_handle.local_atom_id))
    return tuple(sorted(handles, key=handle_key))


@dataclass(frozen=True)
class ReorganizationPlan:
    commands: tuple[object, ...]
    results: tuple[object, ...]
    command_indexes: tuple[int | None, ...]
    final_cells: dict[GeometryAddress, dict[str, MemoryAtom]]
    final_bindings: tuple[HandleBinding, ...]


def project_bindings(
    before: tuple[HandleBinding, ...],
    decisions: tuple[AccessDecision, ...],
    results: tuple[object, ...],
    unavailable_statement_ids: frozenset[str] = frozenset(),
) -> tuple[HandleBinding, ...]:
    """Project only the supplied physical binding scope; outside bindings stay put.

    The caller supplies IDs already bound outside that scope. This keeps a known
    physical-handle operation local while retaining one binding per Statement.
    """
    bindings = {binding.handle: binding for binding in before}
    statement_handles = {
        identity: binding.handle for binding in before
        for identity in (binding.current_statement_id, *binding.supporting_statement_ids)
    }

    def require_unbound(identity):
        if identity in statement_handles or identity in unavailable_statement_ids:
            raise ValueError("statement is already bound")

    def remove(handle):
        binding = bindings.pop(handle)
        for identity in (binding.current_statement_id, *binding.supporting_statement_ids):
            del statement_handles[identity]
        return binding

    def add(binding):
        if binding.handle in bindings:
            raise ValueError("target Core handle is already bound")
        bindings[binding.handle] = binding
        for identity in (binding.current_statement_id, *binding.supporting_statement_ids):
            statement_handles[identity] = binding.handle

    for decision, result in zip(decisions, results):
        action, identity, old = decision.action, decision.statement_id, decision.existing_handle
        if action in {"new", "revision_keep_history"}:
            require_unbound(identity)
            add(HandleBinding(result, identity))
        elif action == "reuse":
            binding = bindings.get(old)
            if binding is not None and binding.current_statement_id == identity:
                continue
            require_unbound(identity)
            if binding is None:
                add(HandleBinding(old, identity))
            else:
                bindings[old] = HandleBinding(
                    old, binding.current_statement_id,
                    tuple(sorted((*binding.supporting_statement_ids, identity))),
                )
                statement_handles[identity] = old
        elif action == "revision_current":
            require_unbound(identity)
            remove(old)
            add(HandleBinding(result, identity))
        elif action in {"move", "forget"}:
            binding = bindings.get(old)
            if binding is None:
                raise KeyError("Core handle has no canonical binding")
            if identity not in (binding.current_statement_id, *binding.supporting_statement_ids):
                raise ValueError("decision statement is not bound to the selected Core handle")
            if action == "move" and old == result:
                continue
            remove(old)
            if action == "move":
                add(HandleBinding(result, binding.current_statement_id, binding.supporting_statement_ids))
    return tuple(sorted(bindings.values(), key=lambda binding: handle_key(binding.handle)))


def project_reorganization(
    decisions: tuple[AccessDecision, ...],
    statements: dict[str, MemoryStatement],
    before_cells: dict[GeometryAddress, dict[str, MemoryAtom]],
    before_bindings: tuple[HandleBinding, ...],
    unavailable_statement_ids: frozenset[str] = frozenset(),
) -> ReorganizationPlan:
    """Plan explicit commands in order, without applying intermediate budgets."""
    cells = {cell: dict(atoms) for cell, atoms in before_cells.items()}
    commands, results, command_indexes = [], [], []
    binding_handles = {binding.handle for binding in before_bindings}

    def atom_at(handle):
        try:
            return cells[handle.geometry_address][handle.local_atom_id]
        except KeyError as error:
            raise KeyError("reorganization selected a missing Core handle") from error

    for decision in decisions:
        action, identity, old = decision.action, decision.statement_id, decision.existing_handle
        command = None
        if action in {"new", "revision_keep_history"}:
            target, statement = decision.target_cell, statements[identity]
            atom = MemoryAtom(identity, statement.content_utf8)
            if identity in cells[target]:
                raise FileExistsError("local atom already exists at target cell")
            cells[target][identity] = atom
            result = AtomHandle(target, identity)
            command = PutCommand(atom, target)
        elif action == "revision_current":
            atom = atom_at(old)
            body = statements[identity].content_utf8
            cells[old.geometry_address][old.local_atom_id] = MemoryAtom(atom.atom_id, body)
            result, command = old, ReplaceCommand(old, body)
        elif action == "move":
            atom, target = atom_at(old), decision.target_cell
            if target != old.geometry_address:
                if old.local_atom_id in cells[target]:
                    raise FileExistsError("local atom already exists at target cell")
                del cells[old.geometry_address][old.local_atom_id]
                cells[target][old.local_atom_id] = atom
            result = AtomHandle(target, old.local_atom_id)
            command = MoveCommand(old, target)
        elif action == "forget":
            result = atom_at(old)
            del cells[old.geometry_address][old.local_atom_id]
            command = RemoveCommand(old)
        elif action == "reuse":
            atom = atom_at(old)
            if old not in binding_handles and statements[identity].content_utf8 != atom.payload_utf8:
                # A first binding becomes current, so its Evidence must describe
                # the actual existing atom rather than only supporting it.
                raise ValueError("first binding Evidence differs from the existing Core payload")
            result = old
        else:
            raise ValueError(f"unsupported reorganization action: {action}")
        command_indexes.append(len(commands) if command is not None else None)
        if command is not None:
            commands.append(command)
        results.append(result)
        if isinstance(result, AtomHandle):
            binding_handles.add(result)
        if action in {"move", "forget"} and (action == "forget" or old != result):
            binding_handles.discard(old)

    projected = project_bindings(before_bindings, decisions, tuple(results), unavailable_statement_ids)
    return ReorganizationPlan(tuple(commands), tuple(results), tuple(command_indexes), cells, projected)
