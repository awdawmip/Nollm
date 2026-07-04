from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from nollm.dream_geometry.field.types import GrowthTrace
from nollm.dream_geometry.geometry.chart import make_hex_cell
from nollm.dream_geometry.geometry.types import AxialCoord, LocalChart, Vec2
from nollm.dream_geometry.protocol.contracts import GrowthBasis, TraceState


def cell(q: int = 0, chart_id: str = "dg5") :
    return make_hex_cell(LocalChart(chart_id, 0, 1.0, 0.0, Vec2(0, 0)), AxialCoord(q, 0))


def trace(trace_id: str, *, support_key: str = "support", axis: str = "axis", q: int = 0, **kwargs) -> GrowthTrace:
    return GrowthTrace(
        trace_id=trace_id,
        origin_shard_id=kwargs.get("origin_shard_id", "origin-a"),
        proposal_id=kwargs.get("proposal_id", "proposal-a"),
        parent_trace_id=kwargs.get("parent_trace_id", "parent-a"),
        cell=kwargs.get("cell", cell(q)),
        axis=axis,
        basis=kwargs.get("basis", GrowthBasis.explicit_in_shard),
        basis_refs=kwargs.get("basis_refs", ("basis-a",)),
        mass=kwargs.get("mass", 0.25),
        support_key=support_key,
        genericity=kwargs.get("genericity", 0.1),
        ambiguity=kwargs.get("ambiguity", 0.1),
        conflict=kwargs.get("conflict", 0.0),
        stability_epochs=kwargs.get("stability_epochs", 2),
        state=kwargs.get("state", TraceState.accepted),
        derivation_kind=kwargs.get("derivation_kind", "synthetic"),
        geometry_refs=kwargs.get("geometry_refs", ("geometry-a",)),
    )


def exact_duplicate_pair() -> tuple[GrowthTrace, GrowthTrace]:
    first = trace("dup-a", mass=0.2)
    return first, replace(first, trace_id="dup-b", mass=0.3)


def mixed_fixture() -> tuple[GrowthTrace, ...]:
    first, second = exact_duplicate_pair()
    passthrough = trace("pass-a", support_key="pass", axis="other", q=1)
    collision = trace("collision-a", support_key="support", origin_shard_id="origin-b")
    same_cell_distinct = trace("same-cell-distinct", proposal_id="proposal-b")
    return (passthrough, collision, second, same_cell_distinct, first)


def trace_index(traces: tuple[GrowthTrace, ...]) -> dict[str, GrowthTrace]:
    return {trace.trace_id: trace for trace in traces}


def stress_fixture(count: int = 1000) -> tuple[GrowthTrace, ...]:
    traces = []
    for index in range(count):
        group = index // 2
        if index < 400:
            base = trace(f"stress-{group:04d}-a", support_key=f"stress-{group:04d}", q=group % 7, mass=0.1)
            traces.append(base if index % 2 == 0 else replace(base, trace_id=f"stress-{group:04d}-b", mass=0.11))
        elif index < 700:
            traces.append(trace(f"pass-{index:04d}", support_key=f"pass-{index:04d}", q=index % 11, axis="pass"))
        else:
            traces.append(trace(f"near-{index:04d}", support_key="near", q=0, origin_shard_id=f"origin-{index:04d}"))
    return tuple(reversed(traces))


def state_dirs(root: Path) -> dict[str, bool]:
    return {name: (root / name).exists() for name in ("evidence", "capture", "field", "admission", "assembly", "recall", "atlas", "state")}
