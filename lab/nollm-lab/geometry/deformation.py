"""Explicit invertible layer maps for Lab geometry experiments.

The contract is float64 similarity/twist mapping followed by Q40 sample
classification. It uses Core's 96 local source samples, tie rule and Q16
normalization, but is not bitwise-equivalent to the fixed production transform
and is not an exact real-area evaluator. No geometry or relation is persisted
implicitly: map parameters have ordinary JSON representations for the caller.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from math import cos, isfinite, pi, sin, sqrt

from nollm_core import (
    GeometryAddress, coverage_sample_offsets_q40, nearest_axial_q40,
    normalize_q16_weights,
)


DEFORMATION_CONTRACT_ID = "lab_float64_layer_map_quadrature_v1"
Q40_ONE = 1 << 40
ROOT3 = sqrt(3)
Point = tuple[float, float]


def _point(value) -> Point:
    x, y = value
    if not isfinite(x) or not isfinite(y):
        raise ValueError("coordinates must be finite")
    return float(x), float(y)


def _rotate(point: Point, angle: float) -> Point:
    c, s = cos(angle), sin(angle)
    return c * point[0] - s * point[1], s * point[0] + c * point[1]


@dataclass(frozen=True)
class SimilarityFrame:
    """world = origin + scale*R(angle)*(local-local_anchor); angle in radians."""

    origin: Point = (0.0, 0.0)
    local_anchor: Point = (0.0, 0.0)
    scale: float = 1.0
    angle: float = 0.0

    def __post_init__(self):
        if not isfinite(self.scale) or self.scale <= 0 or not isfinite(self.angle):
            raise ValueError("frame scale must be positive and scale/angle finite")
        object.__setattr__(self, "origin", _point(self.origin))
        object.__setattr__(self, "local_anchor", _point(self.local_anchor))

    def forward(self, point: Point) -> Point:
        x, y = _rotate((point[0] - self.local_anchor[0],
                        point[1] - self.local_anchor[1]), self.angle)
        return self.origin[0] + self.scale * x, self.origin[1] + self.scale * y

    def inverse(self, point: Point) -> Point:
        x, y = _rotate(((point[0] - self.origin[0]) / self.scale,
                        (point[1] - self.origin[1]) / self.scale), -self.angle)
        return self.local_anchor[0] + x, self.local_anchor[1] + y

    def reanchor(self, local_anchor: Point) -> "SimilarityFrame":
        """Change coordinate representation, preserving every physical point."""
        return replace(self, origin=self.forward(local_anchor), local_anchor=local_anchor)

    def after(self, other: "SimilarityFrame") -> "SimilarityFrame":
        """Return self composed after other, including their anchor offsets."""
        return SimilarityFrame(self.forward(other.origin), other.local_anchor,
                               self.scale * other.scale, self.angle + other.angle)

    def rotate_about(self, center: Point, angle: float) -> "SimilarityFrame":
        """An actual world-space rotation about center, not a passive reanchor."""
        return SimilarityFrame(center, center, 1.0, angle).after(self)

    def to_mapping(self) -> dict:
        return {"origin": list(self.origin), "local_anchor": list(self.local_anchor),
                "scale": self.scale, "angle": self.angle}

    @classmethod
    def from_mapping(cls, value: dict) -> "SimilarityFrame":
        return cls(**value)


@dataclass(frozen=True)
class RadialTwist:
    """Compact C1 twist, angle*(1-r²/radius²)² inside radius and zero outside.

    (r,theta) -> (r,theta+phi(r²)) is globally invertible and preserves the
    area element r dr dtheta. Its analytic determinant is one, including the
    continuous extension at the center. The inverse needs no root finding.
    """

    center: Point = (0.0, 0.0)
    radius: float = 1.0
    angle: float = 0.0

    def __post_init__(self):
        if not isfinite(self.radius) or self.radius <= 0 or not isfinite(self.angle):
            raise ValueError("twist radius must be positive and radius/angle finite")
        object.__setattr__(self, "center", _point(self.center))

    def _map(self, point: Point, sign: int) -> Point:
        delta = point[0] - self.center[0], point[1] - self.center[1]
        if abs(delta[0]) >= self.radius or abs(delta[1]) >= self.radius:
            return point
        # Divide before squaring: the inside-box ratios are bounded, including
        # when a valid small radius would underflow if squared first.
        fraction = (delta[0] / self.radius) ** 2 + (delta[1] / self.radius) ** 2
        if fraction >= 1 or self.angle == 0:
            return point
        moved = _rotate(delta, sign * self.angle * (1 - fraction) ** 2)
        return self.center[0] + moved[0], self.center[1] + moved[1]

    def forward(self, point: Point) -> Point:
        return self._map(point, 1)

    def inverse(self, point: Point) -> Point:
        return self._map(point, -1)

    def with_center(self, center: Point) -> "RadialTwist":
        """Change the physical twist center; this generally changes the map."""
        return replace(self, center=center)

    def to_mapping(self) -> dict:
        return {"center": list(self.center), "radius": self.radius, "angle": self.angle}

    @classmethod
    def from_mapping(cls, value: dict) -> "RadialTwist":
        return cls(**value)


@dataclass(frozen=True)
class LayerMap:
    """A similarity followed by ordered whole-layer, world-coordinate twists."""

    frame: SimilarityFrame = SimilarityFrame()
    twists: tuple[RadialTwist, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "twists", tuple(self.twists))

    @classmethod
    def for_layer(cls, layer: int) -> "LayerMap":
        return cls(SimilarityFrame(scale=2 ** (-layer / 4), angle=layer * pi / 8))

    def forward(self, point: Point) -> Point:
        point = self.frame.forward(point)
        for twist in self.twists:
            point = twist.forward(point)
        return point

    def inverse(self, point: Point) -> Point:
        for twist in reversed(self.twists):
            point = twist.inverse(point)
        return self.frame.inverse(point)

    def with_twist(self, twist: RadialTwist) -> "LayerMap":
        return replace(self, twists=(*self.twists, twist))

    def reanchor(self, local_anchor: Point) -> "LayerMap":
        return replace(self, frame=self.frame.reanchor(local_anchor))

    def to_mapping(self) -> dict:
        return {"contract_id": DEFORMATION_CONTRACT_ID,
                "frame": self.frame.to_mapping(),
                "twists": [twist.to_mapping() for twist in self.twists]}

    @classmethod
    def from_mapping(cls, value: dict) -> "LayerMap":
        if value["contract_id"] != DEFORMATION_CONTRACT_ID:
            raise ValueError("unsupported experimental layer-map contract")
        return cls(SimilarityFrame.from_mapping(value["frame"]),
                   tuple(RadialTwist.from_mapping(item) for item in value["twists"]))


@dataclass(frozen=True)
class SampledMember:
    target: GeometryAddress
    hit_count: int
    weight_q16: int


@dataclass(frozen=True)
class SampledCoverage:
    source: GeometryAddress
    target_layer: int
    members: tuple[SampledMember, ...]
    sample_count: int = 96
    contract_id: str = DEFORMATION_CONTRACT_ID

    def to_mapping(self) -> dict:
        return {"contract_id": self.contract_id, "source": self.source.to_mapping(),
                "target_layer": self.target_layer, "sample_count": self.sample_count,
                "members": [{"target": member.target.to_mapping(),
                             "hit_count": member.hit_count,
                             "weight_q16": member.weight_q16} for member in self.members]}


def sampled_coverage(source: GeometryAddress, target_layer: int,
                     source_map: LayerMap | None = None,
                     target_map: LayerMap | None = None) -> SampledCoverage:
    """Map equal-area source samples through target.inverse(source.forward(x)).

    The target hex has standard axial coordinates. Mapping those coordinates
    to Q40 uses half-even Python round before the original Core cube rounder.
    Shared geometric boundaries are transformed by the same map, so layers
    remain tilings. Curved-cell real-area errors are not certified here.
    """
    if source.profile_id != "default_dream_v1":
        raise ValueError("experimental maps use the default dream hex chart")
    if abs(target_layer - source.layer) != 1 or not -64 <= target_layer <= 64:
        raise ValueError("target must be an admitted adjacent physical layer")
    source_map = source_map or LayerMap.for_layer(source.layer)
    target_map = target_map or LayerMap.for_layer(target_layer)
    center = ROOT3 * (source.q + source.r / 2), 1.5 * source.r
    targets = []
    for dx, dy in coverage_sample_offsets_q40():
        local = center[0] + dx / Q40_ONE, center[1] + dy / Q40_ONE
        x, y = target_map.inverse(source_map.forward(local))
        if not isfinite(x) or not isfinite(y):
            raise ValueError("deformation produced non-finite sample coordinates")
        q, r = x / ROOT3 - y / 3, 2 * y / 3
        targets.append(nearest_axial_q40(round(q * Q40_ONE), round(r * Q40_ONE)))
    counts = sorted(Counter(targets).items())
    weights = normalize_q16_weights([count for _, count in counts])
    members = tuple(SampledMember(
        GeometryAddress(source.profile_id, source.chart_id, target_layer, q, r, source.phase),
        count, weight,
    ) for ((q, r), count), weight in zip(counts, weights))
    return SampledCoverage(source, target_layer, members, len(targets))
