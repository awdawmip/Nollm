"""Compare candidate layer maps on an explicit finite material inventory.

Inputs are physical cells and current unit counts, never text or object routes.
All supplied lower material keeps its complete source-normalized distribution.
An evaluation includes every supplied upper cell and every recipient of that
lower material. Comparisons use the union of both footprints, so changing the
window cannot erase a deficit. No field is written and no move is approved.

``inventory_complete=True`` declares that these dictionaries are the complete
finite inventory of this adjacent layer pair; omitted cells then have zero
units. The default is partial: omitted upper demand is unknown, supplied lower
support is a lower bound, and no total-field deficit/improvement is claimed.
Counts in supplied cells are their exact current counts; partial means omitted
cells, not truncated counts within a supplied cell. Total deficit refers only
to this adjacent layer pair under the stated sampled-coverage contract.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping

from nollm_access import pressure_score
from nollm_core import GeometryAddress, Q16_ONE

from .deformation import (
    DEFORMATION_CONTRACT_ID, LayerMap, sampled_coverage, source_world_samples,
)


Units = Mapping[GeometryAddress, int]
Allocations = dict[tuple[GeometryAddress, GeometryAddress], int]


def _check_cell(cell: GeometryAddress, layer: int) -> None:
    if cell.layer != layer or cell.profile_id != "default_dream_v1":
        raise ValueError("inventory cells must use the selected layer of the default dream chart")


def _check_inputs(upper: Units, lower: Units, upper_layer: int,
                  extra_cells: tuple[GeometryAddress, ...], kappa: int) -> None:
    if not -64 <= upper_layer < 64:
        raise ValueError("evaluation requires an admitted adjacent finer layer")
    pressure_score(0, 0, kappa)
    for inventory, layer in ((upper, upper_layer), (lower, upper_layer + 1)):
        for cell, units in inventory.items():
            _check_cell(cell, layer)
            if not isinstance(units, int) or units < 0:
                raise ValueError("material counts must be nonnegative integers")
    for cell in extra_cells:
        _check_cell(cell, upper_layer)


def _work(mode: str) -> dict:
    if mode not in {"auto", "full"}:
        raise ValueError("mode must be auto or full")
    return {"mode": mode, "reuse_enabled": False,
            "coverage_evaluations": 0, "round_calls": 0,
            "source_sample_maps": 0, "target_sample_maps": 0,
            "same_map_reuses": 0, "outside_twist_reuses": 0,
            "source_sample_reuses": 0, "bounds_checks": 0,
            "peak_cached_source_samples": 0}


def _added_twists(before: LayerMap, after: LayerMap):
    """Return only a literal appended suffix; other map changes need evaluation."""
    count = len(before.twists)
    if before.frame == after.frame and after.twists[:count] == before.twists:
        return after.twists[count:]
    return None


def _bounds(points):
    xs, ys = zip(*points)
    return min(xs), max(xs), min(ys), max(ys)


def _outside_twists(bounds, twists, work) -> bool:
    """Prove every stored sample takes each appended twist's original early exit.

    Subtract the center before comparison, exactly as RadialTwist._map does.
    Testing center +/- radius instead could move a boundary through float
    rounding. Float subtraction is monotone on these finite stored samples.
    If every twist is inactive here, forward and inverse suffixes both leave
    the exact input tuples unchanged; no algebraic cancellation is assumed.
    """
    lo_x, hi_x, lo_y, hi_y = bounds
    for twist in twists:
        work["bounds_checks"] += 1
        if not (lo_x - twist.center[0] >= twist.radius
                or hi_x - twist.center[0] <= -twist.radius
                or lo_y - twist.center[1] >= twist.radius
                or hi_y - twist.center[1] <= -twist.radius):
            return False
    return True


def _allocate(lower: Units, upper_layer: int,
              upper_map: LayerMap, lower_map: LayerMap, *, work: dict,
              geometry_cache=None, sample_cache=None, prior_maps=None) -> Allocations:
    result = {}
    suffixes = None
    if prior_maps is not None:
        old_upper, old_lower = prior_maps
        upper_suffix = _added_twists(old_upper, upper_map)
        lower_suffix = _added_twists(old_lower, lower_map)
        if upper_suffix is not None and lower_suffix is not None:
            suffixes = (*lower_suffix, *upper_suffix)
    for source in sorted(lower, key=GeometryAddress.stable_key):
        if lower[source] == 0:
            continue
        key = (source, upper_layer, lower_map, upper_map)
        coverage = None if geometry_cache is None else geometry_cache.get(key)
        if coverage is not None:
            work["same_map_reuses"] += 1
        elif suffixes is not None:
            old_key = (source, upper_layer, old_lower, old_upper)
            old_samples, bounds = sample_cache[source, old_lower]
            if bounds is None:
                bounds = _bounds(old_samples)
                sample_cache[source, old_lower] = old_samples, bounds
            if _outside_twists(bounds, suffixes, work):
                coverage = geometry_cache[old_key]
                geometry_cache[key] = coverage
                sample_cache[source, lower_map] = old_samples, bounds
                work["outside_twist_reuses"] += 1
        if coverage is None:
            samples = None
            if sample_cache is not None:
                sample_key = source, lower_map
                saved = sample_cache.get(sample_key)
                if saved is None:
                    samples = tuple(source_world_samples(source, lower_map))
                    sample_cache[sample_key] = samples, None
                    work["source_sample_maps"] += len(samples)
                    retained = sum({id(points): len(points)
                                    for points, _ in sample_cache.values()}.values())
                    work["peak_cached_source_samples"] = max(
                        work["peak_cached_source_samples"], retained)
                else:
                    samples = saved[0]
                    work["source_sample_reuses"] += len(samples)
            coverage = sampled_coverage(source, upper_layer, lower_map, upper_map,
                                        world_samples=samples)
            work["coverage_evaluations"] += 1
            work["round_calls"] += coverage.sample_count
            work["target_sample_maps"] += coverage.sample_count
            if sample_cache is None:
                work["source_sample_maps"] += coverage.sample_count
            if geometry_cache is not None:
                geometry_cache[key] = coverage
        for member in coverage.members:
            result[source, member.target] = member.weight_q16
    return result


def _region(upper: Units, extra_cells: Iterable[GeometryAddress],
            *allocations: Allocations) -> tuple[GeometryAddress, ...]:
    cells = set(upper) | set(extra_cells)
    for distribution in allocations:
        cells.update(target for _, target in distribution)
    return tuple(sorted(cells, key=GeometryAddress.stable_key))


def _readout(upper: Units, lower: Units, upper_layer: int,
             upper_map: LayerMap, lower_map: LayerMap,
             allocation: Allocations, region: tuple[GeometryAddress, ...],
             inventory_complete: bool, kappa: int) -> dict:
    support = defaultdict(int)
    allocations = []
    for (source, target), weight in allocation.items():
        mass = lower[source] * weight
        support[target] += mass
        allocations.append({
            "source": source.to_mapping(), "target": target.to_mapping(),
            "source_units": lower[source], "weight_q16": weight,
            "support_q16": mass,
        })
    cells = []
    observed_deficit = 0
    known_pressures = []
    for cell in region:
        demand = upper.get(cell, 0 if inventory_complete else None)
        mass = support[cell]
        score = None if demand is None else pressure_score(demand, mass, kappa)
        if demand is not None:
            observed_deficit += max(demand * Q16_ONE - mass, 0)
            known_pressures.append(score)
        cells.append({
            "cell": cell.to_mapping(), "demand_units": demand,
            "support_q16": mass, "pressure": score,
            "write_weight": None if score is None else 101 - score,
            "support_complete": inventory_complete,
            "score_kind": ("demand_unknown" if demand is None else
                           "complete_finite_inventory" if inventory_complete else "upper_estimate"),
        })
    return {
        "contract_id": DEFORMATION_CONTRACT_ID,
        "upper_layer": upper_layer, "lower_layer": upper_layer + 1,
        "inventory_scope": "complete_finite_inventory" if inventory_complete else "partial_inventory",
        "inventory_complete": inventory_complete,
        "evaluation_region": [cell.to_mapping() for cell in region],
        "cells": cells,
        "supplied_lower_units": sum(lower.values()),
        "distributed_support_q16": sum(support.values()),
        "observed_deficit_q16": observed_deficit,
        "total_deficit_q16": observed_deficit if inventory_complete else None,
        "max_known_pressure": max(known_pressures, default=None),
        "allocations": allocations,
        "maps": {"upper": upper_map.to_mapping(), "lower": lower_map.to_mapping()},
        "advisory": True,
    }


def evaluate_pressure(
    upper_units: Units,
    lower_units: Units,
    *,
    upper_layer: int,
    upper_map: LayerMap | None = None,
    lower_map: LayerMap | None = None,
    inventory_complete: bool = False,
    evaluation_cells: Iterable[GeometryAddress] = (),
    kappa: int = 1,
    mode: str = "auto",
) -> dict:
    """Evaluate current material under one explicit candidate geometry.

    ``evaluation_cells`` can add cells; it never removes supplied demand or
    recipients. To evaluate a proposed write, include its additional units in
    the supplied inventory. This function does not infer semantic placement.
    """
    work = _work(mode)
    extra_cells = tuple(evaluation_cells)
    _check_inputs(upper_units, lower_units, upper_layer, extra_cells, kappa)
    upper_map = upper_map or LayerMap.for_layer(upper_layer)
    lower_map = lower_map or LayerMap.for_layer(upper_layer + 1)
    allocation = _allocate(lower_units, upper_layer, upper_map, lower_map, work=work)
    return {**_readout(upper_units, lower_units, upper_layer, upper_map, lower_map,
                      allocation, _region(upper_units, extra_cells, allocation),
                      inventory_complete, kappa), "work": work}


def compare_pressure(
    upper_units: Units,
    lower_units: Units,
    *,
    upper_layer: int,
    before_upper_map: LayerMap | None = None,
    before_lower_map: LayerMap | None = None,
    after_upper_map: LayerMap | None = None,
    after_lower_map: LayerMap | None = None,
    inventory_complete: bool = False,
    evaluation_cells: Iterable[GeometryAddress] = (),
    kappa: int = 1,
    mode: str = "auto",
) -> dict:
    """Compare fixed material on the union of old and new affected cells.

    An omitted after-map means that layer retains its before-map. A complete
    finite inventory permits a total-deficit difference. Partial inventory
    returns only differences of observed diagnostics; unknown material can
    change their meaning. Neither a lower deficit nor a lower maximum pressure
    automatically approves motion or establishes semantic recall improvement.
    ``auto`` reuses request-local geometry while its inputs stay fixed, and
    excludes appended twists only when their actual early-exit predicates hold
    for all source samples. ``full`` computes both footprints independently.
    Work counts are diagnostics; no inventory or pressure is cached. Each
    source's pair is completed before the next, so retained point samples do
    not grow with the number of sources. Unrelated source-map changes use the
    full path directly when neither source samples nor geometry can be reused.
    """
    work = _work(mode)
    extra_cells = tuple(evaluation_cells)
    _check_inputs(upper_units, lower_units, upper_layer, extra_cells, kappa)
    before_upper_map = before_upper_map or LayerMap.for_layer(upper_layer)
    before_lower_map = before_lower_map or LayerMap.for_layer(upper_layer + 1)
    after_upper_map = after_upper_map or before_upper_map
    after_lower_map = after_lower_map or before_lower_map
    can_reuse = (before_lower_map == after_lower_map or
                 (_added_twists(before_lower_map, after_lower_map) is not None
                  and _added_twists(before_upper_map, after_upper_map) is not None))
    work["reuse_enabled"] = mode == "auto" and can_reuse
    if work["reuse_enabled"]:
        old, new = {}, {}
        for source in sorted(lower_units, key=GeometryAddress.stable_key):
            if lower_units[source] == 0:
                continue
            material = {source: lower_units[source]}
            geometry_cache, sample_cache = {}, {}
            old.update(_allocate(material, upper_layer, before_upper_map, before_lower_map,
                       work=work, geometry_cache=geometry_cache, sample_cache=sample_cache))
            new.update(_allocate(material, upper_layer, after_upper_map, after_lower_map,
                       work=work, geometry_cache=geometry_cache, sample_cache=sample_cache,
                       prior_maps=(before_upper_map, before_lower_map)))
    else:
        old = _allocate(lower_units, upper_layer, before_upper_map, before_lower_map, work=work)
        new = _allocate(lower_units, upper_layer, after_upper_map, after_lower_map, work=work)
    region = _region(upper_units, extra_cells, old, new)
    before = _readout(upper_units, lower_units, upper_layer, before_upper_map, before_lower_map,
                       old, region, inventory_complete, kappa)
    after = _readout(upper_units, lower_units, upper_layer, after_upper_map, after_lower_map,
                      new, region, inventory_complete, kappa)
    changes = []
    keys = sorted(set(old) | set(new), key=lambda pair: (pair[0].stable_key(), pair[1].stable_key()))
    for source, target in keys:
        old_weight, new_weight = old.get((source, target), 0), new.get((source, target), 0)
        if old_weight != new_weight:
            changes.append({
                "source": source.to_mapping(), "target": target.to_mapping(),
                "before_weight_q16": old_weight, "after_weight_q16": new_weight,
                "delta_support_q16": lower_units[source] * (new_weight - old_weight),
            })
    old_max, new_max = before["max_known_pressure"], after["max_known_pressure"]
    return {
        "contract_id": DEFORMATION_CONTRACT_ID,
        "inventory_complete": inventory_complete,
        "region_union": [cell.to_mapping() for cell in region],
        "before": before, "after": after, "coverage_changes": changes,
        "delta": {
            "observed_deficit_q16": after["observed_deficit_q16"] - before["observed_deficit_q16"],
            "total_deficit_q16": (after["total_deficit_q16"] - before["total_deficit_q16"]
                                  if inventory_complete else None),
            "max_known_pressure": None if old_max is None or new_max is None else new_max - old_max,
        },
        "advisory": True,
        "work": work,
    }
