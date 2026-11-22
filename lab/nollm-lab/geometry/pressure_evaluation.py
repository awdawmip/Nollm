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

from .deformation import DEFORMATION_CONTRACT_ID, LayerMap, sampled_coverage


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


def _allocate(lower: Units, upper_layer: int,
              upper_map: LayerMap, lower_map: LayerMap) -> Allocations:
    result = {}
    for source in sorted(lower, key=GeometryAddress.stable_key):
        if lower[source] == 0:
            continue
        coverage = sampled_coverage(source, upper_layer, lower_map, upper_map)
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
) -> dict:
    """Evaluate current material under one explicit candidate geometry.

    ``evaluation_cells`` can add cells; it never removes supplied demand or
    recipients. To evaluate a proposed write, include its additional units in
    the supplied inventory. This function does not infer semantic placement.
    """
    extra_cells = tuple(evaluation_cells)
    _check_inputs(upper_units, lower_units, upper_layer, extra_cells, kappa)
    upper_map = upper_map or LayerMap.for_layer(upper_layer)
    lower_map = lower_map or LayerMap.for_layer(upper_layer + 1)
    allocation = _allocate(lower_units, upper_layer, upper_map, lower_map)
    return _readout(upper_units, lower_units, upper_layer, upper_map, lower_map,
                    allocation, _region(upper_units, extra_cells, allocation),
                    inventory_complete, kappa)


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
) -> dict:
    """Compare fixed material on the union of old and new affected cells.

    An omitted after-map means that layer retains its before-map. A complete
    finite inventory permits a total-deficit difference. Partial inventory
    returns only differences of observed diagnostics; unknown material can
    change their meaning. Neither a lower deficit nor a lower maximum pressure
    automatically approves motion or establishes semantic recall improvement.
    """
    extra_cells = tuple(evaluation_cells)
    _check_inputs(upper_units, lower_units, upper_layer, extra_cells, kappa)
    before_upper_map = before_upper_map or LayerMap.for_layer(upper_layer)
    before_lower_map = before_lower_map or LayerMap.for_layer(upper_layer + 1)
    after_upper_map = after_upper_map or before_upper_map
    after_lower_map = after_lower_map or before_lower_map
    old = _allocate(lower_units, upper_layer, before_upper_map, before_lower_map)
    new = _allocate(lower_units, upper_layer, after_upper_map, after_lower_map)
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
    }
