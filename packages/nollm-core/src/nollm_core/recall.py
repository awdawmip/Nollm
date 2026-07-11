from __future__ import annotations

from dataclasses import dataclass

from .atom import MemoryAtom
from .bridge import Q16_ONE
from .geometry import GeometryAddress
from .coverage_template import expand_template, validate_lateral_ring
from .handle import AtomHandle
from .ports import NullTraceSink, TraceEvent, TraceSink, safe_emit


ALLOWED_KERNELS = frozenset({"coverage_up", "coverage_down", "lateral", "bridge"})


@dataclass(frozen=True)
class RecallBudget:
    max_steps: int
    beam: int
    max_layer_delta: int
    max_lateral_ring: int
    max_bridge_steps: int
    max_results: int

    def __post_init__(self) -> None:
        for value in (self.max_steps, self.beam, self.max_layer_delta, self.max_lateral_ring, self.max_bridge_steps, self.max_results):
            if type(value) is not int or value < 0:
                raise ValueError("Recall budget values must be non-negative integers")
        if self.beam == 0 or self.max_results == 0:
            raise ValueError("beam and max_results must be positive")


@dataclass(frozen=True)
class CoreRecallRequest:
    request_id: str
    entry_cells: tuple[GeometryAddress, ...]
    allowed_kernels: tuple[str, ...]
    budget: RecallBudget

    def __post_init__(self) -> None:
        if not self.request_id or not self.entry_cells:
            raise ValueError("request_id and explicit entry_cells are required")
        if len(set(self.entry_cells)) != len(self.entry_cells):
            raise ValueError("entry_cells must be unique")
        if any(kernel not in ALLOWED_KERNELS for kernel in self.allowed_kernels):
            raise ValueError("unknown Recall kernel")


@dataclass(frozen=True)
class CoreRecallItem:
    handle: AtomHandle
    atom: MemoryAtom
    score_q16: int


@dataclass(frozen=True)
class CoreRecallResult:
    request_id: str
    items: tuple[CoreRecallItem, ...]
    budget_exhausted: bool


def resolve_recall(runtime: object, request: CoreRecallRequest, trace_sink: TraceSink | None = None) -> CoreRecallResult:
    sink = trace_sink or NullTraceSink()
    safe_emit(sink, TraceEvent("core.recall.begin", {"request_id": request.request_id, "entry_count": len(request.entry_cells)}, "stable"))
    if request.budget.max_lateral_ring > 1:
        raise ValueError("only registered lateral ring 1 is supported")
    frontier = [(cell, Q16_ONE, 0, 0) for cell in sorted(request.entry_cells, key=lambda item: item.stable_key())]
    best: dict[GeometryAddress, int] = {}
    found: dict[AtomHandle, CoreRecallItem] = {}
    entry_layers = tuple(cell.layer for cell in request.entry_cells)
    step = 0
    truncated_by_budget = False
    while frontier and step <= request.budget.max_steps:
        merged: dict[GeometryAddress, tuple[int, int]] = {}
        for cell, score, _, bridge_steps in frontier:
            if score <= best.get(cell, -1):
                continue
            best[cell] = score
            for handle, atom in runtime.atoms_at(cell):
                current = found.get(handle)
                if current is None or score > current.score_q16:
                    found[handle] = CoreRecallItem(handle, atom, score)
            if step == request.budget.max_steps:
                if _targets(runtime, cell, request, bridge_steps):
                    truncated_by_budget = True
                continue
            for target, weight, next_bridge_steps in _targets(runtime, cell, request, bridge_steps):
                if min(abs(target.layer - layer) for layer in entry_layers) > request.budget.max_layer_delta:
                    continue
                target_score = score * weight // Q16_ONE
                previous = merged.get(target)
                if previous is None or target_score > previous[0]:
                    merged[target] = (target_score, next_bridge_steps)
        safe_emit(sink, TraceEvent("core.recall.frontier", {"step": step, "cell_count": len(frontier)}, "internal"))
        frontier = [
            (cell, score, step + 1, bridge_steps)
            for cell, (score, bridge_steps) in sorted(merged.items(), key=lambda item: (-item[1][0], item[0].stable_key()))[: request.budget.beam]
            if score > best.get(cell, -1)
        ]
        step += 1
    items = tuple(sorted(found.values(), key=lambda item: (-item.score_q16, item.handle.geometry_address.stable_key(), item.handle.local_atom_id))[: request.budget.max_results])
    exhausted = truncated_by_budget or bool(frontier)
    result = CoreRecallResult(request.request_id, items, exhausted)
    safe_emit(sink, TraceEvent("core.recall.end", {"request_id": request.request_id, "result_count": len(items), "budget_exhausted": exhausted}, "stable"))
    return result


def _targets(runtime: object, cell: GeometryAddress, request: CoreRecallRequest, bridge_steps: int) -> tuple[tuple[GeometryAddress, int, int], ...]:
    output: list[tuple[GeometryAddress, int, int]] = []
    if "coverage_up" in request.allowed_kernels:
        template = runtime.kernel_registry.coverage_template(cell.profile_id, "coverage_up")
        output.extend((target, weight, bridge_steps) for target, weight in expand_template(cell, template))
    if "coverage_down" in request.allowed_kernels:
        template = runtime.kernel_registry.coverage_template(cell.profile_id, "coverage_down")
        output.extend((target, weight, bridge_steps) for target, weight in expand_template(cell, template))
    if "lateral" in request.allowed_kernels:
        for ring in range(1, request.budget.max_lateral_ring + 1):
            validate_lateral_ring(ring, runtime.kernel_registry.fanout_limit)
            template = runtime.kernel_registry.coverage_template(cell.profile_id, "lateral")
            output.extend((target, weight, bridge_steps) for target, weight in expand_template(cell, template))
    if "bridge" in request.allowed_kernels and bridge_steps < request.budget.max_bridge_steps:
        for bridge in runtime.bridges():
            if cell not in bridge.from_anchor.cells or bridge_steps >= bridge.max_steps:
                continue
            for target in sorted(bridge.to_anchor.cells, key=lambda item: item.stable_key())[: bridge.max_fanout]:
                output.append((target, bridge.weight_q16, bridge_steps + 1))
    return tuple(output)
