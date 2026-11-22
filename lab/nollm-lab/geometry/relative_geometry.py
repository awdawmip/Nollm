"""Relative world coordinates for float64 candidate layer-map coverage.

Subtract the target frame's world origin before evaluating either layer. A
common world translation commutes with every similarity and radial twist when
their world origins/centers are translated together. Local anchors, scales,
angles and map order stay unchanged, so this changes only the arithmetic
representation of the same ideal relative geometry.

The separate v2 contract avoids adding small samples to a huge common world
anchor and then subtracting it. It can differ from the v1 float64 evaluation
order. Already-rounded input coordinates cannot reveal a lost relative offset;
this is still float64 quadrature, not an exact real-area or exact-float solver.
The maps and the persisted Core field are not modified.
"""
from __future__ import annotations

from dataclasses import replace
from math import isfinite

from nollm_core import GeometryAddress

from .deformation import LayerMap, SampledCoverage, sampled_coverage


RELATIVE_DEFORMATION_CONTRACT_ID = "lab_float64_relative_layer_map_quadrature_v2"


def _relative_point(point, anchor):
    result = point[0] - anchor[0], point[1] - anchor[1]
    if not all(isfinite(value) for value in result):
        raise ValueError("relative world coordinates must remain finite after anchor subtraction")
    return result


def _rebase_world(mapping: LayerMap, anchor) -> LayerMap:
    frame = replace(mapping.frame, origin=_relative_point(mapping.frame.origin, anchor))
    twists = tuple(replace(twist, center=_relative_point(twist.center, anchor))
                   for twist in mapping.twists)
    return LayerMap(frame, twists)


def relative_layer_maps(source_map: LayerMap, target_map: LayerMap) -> tuple[LayerMap, LayerMap]:
    """Re-express both maps around ``target_map.frame.origin``.

    The returned target frame has world origin (0, 0). Twist centers are world
    points and move with that origin; local anchors are local coordinates and
    are left as supplied. Finite inputs whose differences overflow float64
    raise a numerical-domain error rather than returning a fictitious map.
    """
    anchor = target_map.frame.origin
    return _rebase_world(source_map, anchor), _rebase_world(target_map, anchor)


def sampled_relative_coverage(
    source: GeometryAddress,
    target_layer: int,
    source_map: LayerMap | None = None,
    target_map: LayerMap | None = None,
) -> SampledCoverage:
    """Sample candidate coverage under the explicit relative-coordinate v2 contract.

    Defaults select the same ideal default layer maps as v1. They do not change
    Core's admitted geometry or silently opt a v1 caller into new arithmetic.
    """
    source_map = source_map or LayerMap.for_layer(source.layer)
    target_map = target_map or LayerMap.for_layer(target_layer)
    relative_source, relative_target = relative_layer_maps(source_map, target_map)
    result = sampled_coverage(source, target_layer, relative_source, relative_target)
    return replace(result, contract_id=RELATIVE_DEFORMATION_CONTRACT_ID)
