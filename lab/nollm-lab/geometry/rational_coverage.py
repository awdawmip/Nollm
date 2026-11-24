"""Rational axial quadrature and advisory support pressure for Lab.

Maps are explicit rational maps, not an implicit rational replacement of the
default 22.5-degree / fourth-root scale profile. The 96 rational centroids form
an exact equal-area stencil in the undeformed hexagon. Their transformed target
assignments are exact in auto/reference/adaptive modes. The explicit quantized
mode accepts a single fixed-precision nonlinear evaluation with its own contract.
Hit shares are exact for the selected stencil execution; curved-cell overlap
area is still sampled. Q16 weights are an output projection and never feed pressure.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache

from nollm_core import GeometryAddress, normalize_q16_weights

from .adaptive_rational_kernel import compile_adaptive_pair
from .local_quantized_rational_kernel import (
    LOCAL_QUANTIZED_CONTRACT_ID, compile_local_quantized_pair,
)
from .quantized_rational_kernel import compile_quantized_pair
from .rational_affine_kernel import compile_affine_pair
from .rational_geometry import Q, RationalLayerMap, rational_to_mapping


RATIONAL_COVERAGE_CONTRACT_ID = "lab_exact_rational_axial_quadrature_v1"
QUANTIZED_COVERAGE_CONTRACT_ID = "lab_quantized_rational_axial_quadrature_v1"
SAMPLE_COUNT = 96
Units = Mapping[GeometryAddress, int]
Allocations = dict[tuple[GeometryAddress, GeometryAddress], Fraction]


def _fractional_precision(mode, fractional_bits):
    if mode not in {"quantized", "local_quantized"}:
        return None
    return (8 if mode == "local_quantized" else 12) if fractional_bits is None else fractional_bits


def _execution_metadata(fractional_bits=None, local_length=None):
    if local_length is not None:
        return {"contract_id": LOCAL_QUANTIZED_CONTRACT_ID,
                "share_basis": "local_quantized_sample_share", "fractional_bits": fractional_bits,
                "local_length": rational_to_mapping(local_length),
                "anchor_policy": "source_cell_affine_center",
                "target_anchor_policy": "even_integer"}
    if fractional_bits is None:
        return {"contract_id": RATIONAL_COVERAGE_CONTRACT_ID,
                "share_basis": "exact_sample_share"}
    return {"contract_id": QUANTIZED_COVERAGE_CONTRACT_ID,
            "share_basis": "quantized_sample_share", "fractional_bits": fractional_bits}


@lru_cache(maxsize=1)
def rational_sample_offsets() -> tuple[tuple[Fraction, Fraction], ...]:
    """Six sectors, each split into 16 equal-area triangles; denominator 36."""
    vertices = ((1, 1), (-1, 2), (-2, 1), (-1, -1), (1, -2), (2, -1))
    offsets = []
    for sector, first in enumerate(vertices):
        second = vertices[(sector + 1) % 6]
        for count, extra in ((4, 1), (3, 2)):
            for i in range(count):
                for j in range(count - i):
                    a, b = 3 * i + extra, 3 * j + extra
                    offsets.append((Fraction(a * first[0] + b * second[0], 36),
                                    Fraction(a * first[1] + b * second[1], 36)))
    return tuple(offsets)


@lru_cache(maxsize=1)
def rational_sample_numerators() -> tuple[tuple[int, int], ...]:
    """The same 96 labeled offsets, sharing denominator 36 for integer kernels."""
    return tuple((q.numerator*(36//q.denominator), r.numerator*(36//r.denominator))
                 for q, r in rational_sample_offsets())


def _half_even(value: Fraction) -> int:
    sign = -1 if value < 0 else 1
    whole, remainder = divmod(abs(value.numerator), value.denominator)
    twice = 2 * remainder
    if twice > value.denominator or (twice == value.denominator and whole % 2):
        whole += 1
    return sign * whole


def nearest_axial_rational(q, r) -> tuple[int, int]:
    """Exact cube rounding, with the existing q-then-r error tie priority.

    No Q40 projection occurs before this decision. Thus near a half-cell face
    this contract can intentionally differ from quantize-then-round kernels.
    """
    q, r = Q(q), Q(r)
    y = -q - r
    iq, ir, iy = _half_even(q), _half_even(r), _half_even(y)
    dq, dr, dy = abs(iq - q), abs(ir - r), abs(iy - y)
    if dq >= dr and dq >= dy:
        iq = -iy - ir
    elif dr >= dy:
        ir = -iq - iy
    return iq, ir


@dataclass(frozen=True)
class RationalMember:
    target: GeometryAddress
    hit_count: int
    weight: Fraction
    weight_q16: int


@dataclass(frozen=True)
class RationalCoverage:
    source: GeometryAddress
    target_layer: int
    members: tuple[RationalMember, ...]
    sample_count: int = SAMPLE_COUNT
    contract_id: str = RATIONAL_COVERAGE_CONTRACT_ID
    fractional_bits: int | None = None
    local_length: Fraction | None = None

    def to_mapping(self) -> dict:
        result = {**_execution_metadata(self.fractional_bits, self.local_length),
                "contract_id": self.contract_id, "source": self.source.to_mapping(),
                "target_layer": self.target_layer, "sample_count": self.sample_count,
                "members": [
                    {"target": member.target.to_mapping(), "hit_count": member.hit_count,
                     "weight": rational_to_mapping(member.weight),
                     "weight_q16": member.weight_q16} for member in self.members]}
        if self.fractional_bits is not None:
            result["fractional_bits"] = self.fractional_bits
        return result


def sampled_rational_coverage(
    source: GeometryAddress, target_layer: int,
    source_map: RationalLayerMap, target_map: RationalLayerMap,
    *, mode: str = "auto", initial_bits: int = 16, max_bits: int = 128,
    fractional_bits: int | None = None, local_length=None,
) -> RationalCoverage:
    """Classify all 96 mapped centroids under two explicit layer maps.

    Common maps and common world translations cancel algebraically, including
    integer origins larger than float64 can resolve. The returned addresses
    still use GeometryAddress's existing admitted storage domain.
    ``auto`` compiles the relative affine map when no distinct twists remain;
    ``reference`` evaluates every rational map operation. Both have exactly
    the same input/output contract. Other twist pairs use the reference path.
    ``adaptive`` evaluates distinct twists with outward-rounded integer
    intervals, increasing precision only for unresolved samples and finally
    evaluating their exact rational labels if needed. Its bit settings control
    work, not the accuracy of the returned sample labels or shares.
    ``quantized`` instead accepts one nonlinear fixed-point pass at
    fractional_bits (default 12), with no certification or repair. Its outputs carry a
    separate contract ID and the chosen precision. Pure affine pairs retain
    the exact integer kernel in this mode.
    ``local_quantized`` defaults to 8 bits in an explicitly supplied positive
    ``local_length`` of the source layer. Each cell uses its pre-twist affine
    center as the quantization anchor; full target addresses remain exact.
    Common world scaling must also scale local_length. Its output records
    this unit and a separate versioned local-quantization contract.
    """
    if source.profile_id != "default_dream_v1":
        raise ValueError("rational quadrature requires the default axial address chart")
    if abs(target_layer - source.layer) != 1 or not -64 <= target_layer <= 64:
        raise ValueError("target must be an admitted adjacent physical layer")
    fractional_bits = _fractional_precision(mode, fractional_bits)
    kernel = _select_kernel(source_map, target_map, mode, initial_bits, max_bits,
                            fractional_bits, local_length)
    return _sampled(source, target_layer, source_map, target_map, kernel,
                    fractional_bits, kernel.local_length if mode == "local_quantized" else None)


def _select_kernel(source_map, target_map, mode, initial_bits=16, max_bits=128,
                   fractional_bits=None, local_length=None):
    fractional_bits = _fractional_precision(mode, fractional_bits)
    if mode == "local_quantized":
        if local_length is None:
            raise ValueError("local_quantized requires the source layer's positive local_length")
        return compile_local_quantized_pair(source_map, target_map,
                                             local_length=local_length, fractional_bits=fractional_bits)
    if local_length is not None:
        raise ValueError("local_length applies to local_quantized mode")
    if mode == "quantized":
        return compile_quantized_pair(source_map, target_map, fractional_bits=fractional_bits)
    if mode == "adaptive":
        return compile_adaptive_pair(source_map, target_map,
                                     initial_bits=initial_bits, max_bits=max_bits)
    if mode not in {"auto", "reference"}:
        raise ValueError("mode must be auto, reference, adaptive, quantized or local_quantized")
    return compile_affine_pair(source_map, target_map) if mode == "auto" else None


def _sampled(source, target_layer, source_map, target_map, kernel, fractional_bits=None,
             local_length=None):
    if kernel is not None:
        counts = Counter(kernel.targets(source.q, source.r, rational_sample_numerators(), 36))
    else:
        counts = Counter()
        for q, r in rational_sample_offsets():
            point = source.q + q, source.r + r
            target = target_map.inverse(source_map.forward(point))
            counts[nearest_axial_rational(*target)] += 1
    ordered = sorted(counts.items())
    weights_q16 = normalize_q16_weights([count for _, count in ordered])
    members = tuple(RationalMember(
        GeometryAddress(source.profile_id, source.chart_id, target_layer, q, r, source.phase),
        count, Fraction(count, SAMPLE_COUNT), weight_q16,
    ) for ((q, r), count), weight_q16 in zip(ordered, weights_q16))
    return RationalCoverage(source, target_layer, members,
                            contract_id=_execution_metadata(fractional_bits, local_length)["contract_id"],
                            fractional_bits=fractional_bits, local_length=local_length)


def rational_pressure_score(demand, support, kappa=1) -> Fraction:
    """Exact advisory score; inputs are exact nonnegative material quantities."""
    demand, support, kappa = Q(demand), Q(support), Q(kappa)
    if demand < 0 or support < 0 or kappa <= 0:
        raise ValueError("demand/support must be nonnegative and kappa positive")
    return 1 + 99 * max(demand - support, 0) / (demand + kappa)


def pressure_display(exact_score: Fraction) -> int:
    """Round a computed nonnegative score half-up, only at the display boundary."""
    whole, remainder = divmod(exact_score.numerator, exact_score.denominator)
    return whole + int(2 * remainder >= exact_score.denominator)


def _check_inputs(upper: Units, lower: Units, upper_layer: int,
                  extra_cells: tuple[GeometryAddress, ...], kappa) -> Fraction:
    if not -64 <= upper_layer < 64:
        raise ValueError("evaluation requires an admitted adjacent finer layer")
    kappa = Q(kappa)
    rational_pressure_score(0, 0, kappa)
    for inventory, layer in ((upper, upper_layer), (lower, upper_layer + 1)):
        for cell, units in inventory.items():
            if cell.layer != layer or cell.profile_id != "default_dream_v1":
                raise ValueError("inventory cells must use the selected default axial layer")
            if not isinstance(units, int) or units < 0:
                raise ValueError("current material counts must be nonnegative integers")
    if any(cell.layer != upper_layer or cell.profile_id != "default_dream_v1"
           for cell in extra_cells):
        raise ValueError("evaluation cells must use the selected upper layer")
    return kappa


def _allocate(lower: Units, upper_layer: int,
              upper_map: RationalLayerMap, lower_map: RationalLayerMap, mode: str,
              initial_bits: int = 16, max_bits: int = 128,
              fractional_bits: int | None = None, local_length=None) -> Allocations:
    result = {}
    # One compilation per map pair/request; it is independent of inventory.
    fractional_bits = _fractional_precision(mode, fractional_bits)
    kernel = _select_kernel(lower_map, upper_map, mode, initial_bits, max_bits,
                            fractional_bits, local_length)
    for source in sorted(lower, key=GeometryAddress.stable_key):
        if lower[source]:
            coverage = _sampled(source, upper_layer, lower_map, upper_map, kernel,
                                fractional_bits, kernel.local_length if mode == "local_quantized" else None)
            result.update({(source, member.target): member.weight for member in coverage.members})
    return result


def _region(upper: Units, extra_cells: Iterable[GeometryAddress], *allocations):
    cells = set(upper) | set(extra_cells)
    for allocation in allocations:
        cells.update(target for _, target in allocation)
    return tuple(sorted(cells, key=GeometryAddress.stable_key))


def _readout(upper, lower, upper_layer, upper_map, lower_map,
             allocation, region, inventory_complete, kappa, fractional_bits=None, local_length=None):
    support = defaultdict(Fraction)
    allocations = []
    for (source, target), weight in allocation.items():
        mass = lower[source] * weight
        support[target] += mass
        allocations.append({"source": source.to_mapping(), "target": target.to_mapping(),
                            "source_units": lower[source], "weight": rational_to_mapping(weight),
                            "support": rational_to_mapping(mass)})
    cells, scores = [], []
    observed_deficit = Fraction(0)
    for cell in region:
        demand = upper.get(cell, 0 if inventory_complete else None)
        mass = support[cell]
        score = None if demand is None else rational_pressure_score(demand, mass, kappa)
        display = None if score is None else pressure_display(score)
        if demand is not None:
            observed_deficit += max(demand - mass, 0)
            scores.append(display)
        cells.append({"cell": cell.to_mapping(), "demand_units": demand,
                      "support": rational_to_mapping(mass),
                      "pressure_exact": None if score is None else rational_to_mapping(score),
                      "pressure": display, "write_weight": None if display is None else 101 - display,
                      "support_complete": inventory_complete,
                      "score_kind": ("demand_unknown" if demand is None else
                                     "complete_finite_inventory" if inventory_complete else "upper_estimate")})
    return {**_execution_metadata(fractional_bits, local_length),
            "upper_layer": upper_layer, "lower_layer": upper_layer + 1,
            "inventory_complete": inventory_complete,
            "inventory_scope": "complete_finite_inventory" if inventory_complete else "partial_inventory",
            "evaluation_region": [cell.to_mapping() for cell in region], "cells": cells,
            "supplied_lower_units": sum(lower.values()),
            "distributed_support": rational_to_mapping(sum(support.values(), Fraction(0))),
            "observed_deficit": rational_to_mapping(observed_deficit),
            "total_deficit": rational_to_mapping(observed_deficit) if inventory_complete else None,
            "max_known_pressure": max(scores, default=None), "allocations": allocations,
            "maps": {"upper": upper_map.to_mapping(), "lower": lower_map.to_mapping()},
            "kappa": rational_to_mapping(kappa), "advisory": True}, observed_deficit


def evaluate_rational_pressure(
    upper_units: Units, lower_units: Units, *, upper_layer: int,
    upper_map: RationalLayerMap, lower_map: RationalLayerMap,
    inventory_complete: bool = False,
    evaluation_cells: Iterable[GeometryAddress] = (), kappa=1,
    mode: str = "auto", initial_bits: int = 16, max_bits: int = 128,
    fractional_bits: int | None = None, local_length=None,
) -> dict:
    """Evaluate explicit current counts, keeping exact sampled support fractions.

    Omitted cells have zero units only for a declared complete finite layer-pair
    inventory. Otherwise omitted demand is unknown, supplied support is a lower
    bound and no whole-inventory deficit is returned. Proposed extra writes
    must be included in the caller's counts; no semantic placement is inferred.
    In quantized mode support and pressure are exact fractions of the accepted
    quantized sample counts, which may differ from the exact-map counts.
    In local_quantized mode local_length describes the lower/source layer.
    """
    extra = tuple(evaluation_cells)
    kappa = _check_inputs(upper_units, lower_units, upper_layer, extra, kappa)
    fractional_bits = _fractional_precision(mode, fractional_bits)
    allocation = _allocate(lower_units, upper_layer, upper_map, lower_map, mode,
                           initial_bits, max_bits, fractional_bits, local_length)
    return _readout(upper_units, lower_units, upper_layer, upper_map, lower_map,
                    allocation, _region(upper_units, extra, allocation), inventory_complete, kappa,
                    fractional_bits, Q(local_length) if mode == "local_quantized" else None)[0]


def compare_rational_pressure(
    upper_units: Units, lower_units: Units, *, upper_layer: int,
    before_upper_map: RationalLayerMap, before_lower_map: RationalLayerMap,
    after_upper_map: RationalLayerMap | None = None,
    after_lower_map: RationalLayerMap | None = None,
    inventory_complete: bool = False,
    evaluation_cells: Iterable[GeometryAddress] = (), kappa=1,
    mode: str = "auto", initial_bits: int = 16, max_bits: int = 128,
    fractional_bits: int | None = None, local_length=None, after_local_length=None,
) -> dict:
    """Compare maps using the same material and the union of both full footprints.

    Every request computes geometry and current material. ``auto`` uses the
    exact integer affine kernel when applicable; ``reference`` evaluates all
    rational map operations. ``adaptive`` keeps the same exact output through
    interval filtering and per-sample precision escalation/fallback. There is
    no persistent relation cache or move. ``quantized`` accepts the distinct
    fixed-precision sampled geometry without correcting changed sample labels.
    local_quantized uses local_length for the before lower/source map and
    after_local_length for the after map (defaulting to the same unit).
    """
    extra = tuple(evaluation_cells)
    kappa = _check_inputs(upper_units, lower_units, upper_layer, extra, kappa)
    fractional_bits = _fractional_precision(mode, fractional_bits)
    if after_local_length is not None and mode != "local_quantized":
        raise ValueError("after_local_length applies to local_quantized mode")
    after_local_length = local_length if after_local_length is None else after_local_length
    after_upper_map = before_upper_map if after_upper_map is None else after_upper_map
    after_lower_map = before_lower_map if after_lower_map is None else after_lower_map
    old = _allocate(lower_units, upper_layer, before_upper_map, before_lower_map, mode,
                    initial_bits, max_bits, fractional_bits, local_length)
    new = _allocate(lower_units, upper_layer, after_upper_map, after_lower_map, mode,
                    initial_bits, max_bits, fractional_bits, after_local_length)
    region = _region(upper_units, extra, old, new)
    before, old_deficit = _readout(upper_units, lower_units, upper_layer, before_upper_map,
                                   before_lower_map, old, region, inventory_complete, kappa,
                                   fractional_bits, Q(local_length) if mode == "local_quantized" else None)
    after, new_deficit = _readout(upper_units, lower_units, upper_layer, after_upper_map,
                                 after_lower_map, new, region, inventory_complete, kappa,
                                 fractional_bits, Q(after_local_length) if mode == "local_quantized" else None)
    changes = []
    for source, target in sorted(set(old) | set(new),
                                 key=lambda pair: (pair[0].stable_key(), pair[1].stable_key())):
        old_weight, new_weight = old.get((source, target), Fraction(0)), new.get((source, target), Fraction(0))
        if old_weight != new_weight:
            changes.append({"source": source.to_mapping(), "target": target.to_mapping(),
                            "before_weight": rational_to_mapping(old_weight),
                            "after_weight": rational_to_mapping(new_weight),
                            "delta_support": rational_to_mapping(lower_units[source] * (new_weight - old_weight))})
    old_max, new_max = before["max_known_pressure"], after["max_known_pressure"]
    delta_deficit = rational_to_mapping(new_deficit - old_deficit)
    return {**_execution_metadata(fractional_bits, Q(local_length) if mode == "local_quantized" else None),
            "inventory_complete": inventory_complete, "region_union": [cell.to_mapping() for cell in region],
            "before": before, "after": after, "coverage_changes": changes,
            "delta": {"observed_deficit": delta_deficit,
                      "total_deficit": delta_deficit if inventory_complete else None,
                      "max_known_pressure": None if old_max is None or new_max is None else new_max - old_max},
            "advisory": True}

