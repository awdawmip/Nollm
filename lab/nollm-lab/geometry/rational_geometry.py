"""Exact rational maps in the triangular lattice's axial coordinates.

The metric is N(q, r) = q*q + q*r + r*r. Its coefficients, the hexagon's
vertices and the maps below are rational; no Cartesian sqrt(3) is evaluated.
For J = ((-1, -2), (2, 1)), J*J = -3I. The rational Cayley family

    C(t) = ((1 - 3*t*t) I + 2*t*J) / (1 + 3*t*t)

has determinant one and preserves N. In a Cartesian interpretation its angle
is 2*atan(sqrt(3)*t). A rational t therefore defines its own exact rotation;
it does not exactly encode the production 22.5-degree rotation in general.

All arithmetic here uses Fraction. Denominators may grow during nonlinear
composition: exact arithmetic is not a claim of bounded execution cost.
These explicit Lab maps do not change the persisted Core geometry profile.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from fractions import Fraction


RATIONAL_MAP_CONTRACT_ID = "lab_exact_rational_axial_map_v1"
RationalInput = int | Fraction | str
Point = tuple[Fraction, Fraction]
Matrix = tuple[Point, Point]


def Q(value: RationalInput) -> Fraction:
    """Accept an exact integer/fraction or a decimal/fraction text value.

    A float has already selected a binary approximation. Reject it here so
    the caller explicitly chooses the intended rational value at the input.
    """
    if isinstance(value, Fraction):
        return value
    if isinstance(value, (int, str)):
        return Fraction(value)
    raise TypeError("rational input requires int, Fraction or text; float is not accepted")


def rational_to_mapping(value: RationalInput) -> dict[str, str]:
    """String components survive JSON readers whose numbers stop at 2**53."""
    value = Q(value)
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def rational_from_mapping(value: dict[str, str]) -> Fraction:
    numerator, denominator = value["numerator"], value["denominator"]
    if not isinstance(numerator, str) or not isinstance(denominator, str):
        raise TypeError("serialized rational numerator and denominator must be strings")
    return Fraction(int(numerator), int(denominator))


def _point(value) -> Point:
    q, r = value
    return Q(q), Q(r)


def _matrix(value) -> Matrix:
    first, second = value
    return _point(first), _point(second)


def _apply(matrix: Matrix, point: Point) -> Point:
    (a, b), (c, d) = matrix
    q, r = point
    return a*q+b*r, c*q+d*r


def _multiply(first: Matrix, second: Matrix) -> Matrix:
    (a, b), (c, d) = first
    (e, f), (g, h) = second
    return (a*e+b*g, a*f+b*h), (c*e+d*g, c*f+d*h)


def _point_mapping(point: Point) -> list[dict[str, str]]:
    return [rational_to_mapping(value) for value in point]


def _point_from_mapping(value) -> Point:
    q, r = value
    return rational_from_mapping(q), rational_from_mapping(r)


def axial_norm2(point) -> Fraction:
    """Triangular axial metric; standard pointy-hex Cartesian norm² is 3*N."""
    q, r = _point(point)
    return q*q+q*r+r*r


def rational_rotation(parameter: RationalInput) -> Matrix:
    """Return the exact, metric-preserving rotation C(parameter)."""
    t = Q(parameter)
    middle, divisor = 1-3*t*t, 1+3*t*t
    return ((middle-2*t)/divisor, -4*t/divisor), (4*t/divisor, (middle+2*t)/divisor)


@dataclass(frozen=True)
class RationalAffine:
    """world = origin + matrix*(local-local_anchor), all in axial units."""

    matrix: Matrix = ((1, 0), (0, 1))
    origin: Point = (0, 0)
    local_anchor: Point = (0, 0)
    _inverse_matrix: Matrix = field(init=False, repr=False, compare=False)
    _determinant: Fraction = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        matrix = _matrix(self.matrix)
        (a, b), (c, d) = matrix
        determinant = a*d-b*c
        if determinant == 0:
            raise ValueError("rational affine matrix must be invertible")
        object.__setattr__(self, "matrix", matrix)
        object.__setattr__(self, "origin", _point(self.origin))
        object.__setattr__(self, "local_anchor", _point(self.local_anchor))
        object.__setattr__(self, "_determinant", determinant)
        object.__setattr__(self, "_inverse_matrix",
                           ((d/determinant, -b/determinant),
                            (-c/determinant, a/determinant)))

    @property
    def determinant(self) -> Fraction:
        return self._determinant

    @classmethod
    def similarity(cls, scale: RationalInput = 1, rotation_parameter: RationalInput = 0,
                   *, origin=(0, 0), local_anchor=(0, 0)) -> "RationalAffine":
        scale = Q(scale)
        if scale <= 0:
            raise ValueError("similarity scale must be positive")
        rotation = rational_rotation(rotation_parameter)
        matrix = tuple(tuple(scale*value for value in row) for row in rotation)
        return cls(matrix, origin, local_anchor)

    def forward(self, point) -> Point:
        q, r = _point(point)
        mapped = _apply(self.matrix, (q-self.local_anchor[0], r-self.local_anchor[1]))
        return self.origin[0]+mapped[0], self.origin[1]+mapped[1]

    def inverse(self, point) -> Point:
        q, r = _point(point)
        mapped = _apply(self._inverse_matrix, (q-self.origin[0], r-self.origin[1]))
        return self.local_anchor[0]+mapped[0], self.local_anchor[1]+mapped[1]

    def inverse_frame(self) -> "RationalAffine":
        """Return the exact inverse as a composable affine value."""
        return RationalAffine(self._inverse_matrix, self.local_anchor, self.origin)

    def reanchor(self, local_anchor) -> "RationalAffine":
        """Change the local representation while preserving every mapped point."""
        local_anchor = _point(local_anchor)
        return replace(self, origin=self.forward(local_anchor), local_anchor=local_anchor)

    def after(self, other: "RationalAffine") -> "RationalAffine":
        """Return self composed after other, including both anchor offsets."""
        return RationalAffine(_multiply(self.matrix, other.matrix),
                              self.forward(other.origin), other.local_anchor)

    def to_mapping(self) -> dict:
        return {"matrix": [_point_mapping(row) for row in self.matrix],
                "origin": _point_mapping(self.origin),
                "local_anchor": _point_mapping(self.local_anchor)}

    @classmethod
    def from_mapping(cls, value: dict) -> "RationalAffine":
        return cls(tuple(_point_from_mapping(row) for row in value["matrix"]),
                   _point_from_mapping(value["origin"]),
                   _point_from_mapping(value["local_anchor"]))


@dataclass(frozen=True)
class RationalRadialTwist:
    """Compact radial twist using a rational function of the axial radius².

    For s=N(point-center)<radius_squared, t=strength*(1-s/radius_squared)**2
    and the point is rotated by C(t). Outside, the map is the identity.
    radius_squared is in N units: an old Cartesian radius R corresponds to
    R²/3 under the standard pointy-hex embedding, not to R².
    N is exactly preserved, so the inverse uses -strength without root finding.
    In polar coordinates it is (r,theta)->(r,theta+phi(r²)); its determinant
    is one. The squared cutoff makes the derivative join the identity at the
    support boundary. This radial law differs from the float v1 angle law.

    The determinant also follows without trigonometry: C^-1*C' is
    2J/(1+3t²), and u^T*G*J*u=0 for N(u)=u^T*G*u. The radial derivative is
    a rank-one Jacobian correction with zero determinant-lemma contribution.
    """

    center: Point = (0, 0)
    radius_squared: Fraction = Fraction(1)
    strength: Fraction = Fraction(0)

    def __post_init__(self):
        radius_squared = Q(self.radius_squared)
        if radius_squared <= 0:
            raise ValueError("twist radius_squared must be positive")
        object.__setattr__(self, "center", _point(self.center))
        object.__setattr__(self, "radius_squared", radius_squared)
        object.__setattr__(self, "strength", Q(self.strength))

    def _map(self, point, sign: int) -> Point:
        point = _point(point)
        delta = point[0]-self.center[0], point[1]-self.center[1]
        radius = axial_norm2(delta)
        if radius >= self.radius_squared or self.strength == 0:
            return point
        parameter = sign*self.strength*(1-radius/self.radius_squared)**2
        moved = _apply(rational_rotation(parameter), delta)
        return self.center[0]+moved[0], self.center[1]+moved[1]

    def forward(self, point) -> Point:
        return self._map(point, 1)

    def inverse(self, point) -> Point:
        return self._map(point, -1)

    def with_center(self, center) -> "RationalRadialTwist":
        """Move the physical support center, rather than re-expressing coordinates."""
        return replace(self, center=center)

    def to_mapping(self) -> dict:
        return {"center": _point_mapping(self.center),
                "radius_squared": rational_to_mapping(self.radius_squared),
                "strength": rational_to_mapping(self.strength)}

    @classmethod
    def from_mapping(cls, value: dict) -> "RationalRadialTwist":
        return cls(_point_from_mapping(value["center"]),
                   rational_from_mapping(value["radius_squared"]),
                   rational_from_mapping(value["strength"]))


@dataclass(frozen=True)
class RationalLayerMap:
    """An explicit rational affine frame followed by ordered world twists.

    There is deliberately no default for_layer conversion: the original
    irrational layer scale/angle and these rational maps are distinct inputs.
    """

    frame: RationalAffine = RationalAffine()
    twists: tuple[RationalRadialTwist, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "twists", tuple(self.twists))

    def forward(self, point) -> Point:
        point = self.frame.forward(point)
        for twist in self.twists:
            point = twist.forward(point)
        return point

    def inverse(self, point) -> Point:
        point = _point(point)
        for twist in reversed(self.twists):
            point = twist.inverse(point)
        return self.frame.inverse(point)

    def with_twist(self, twist: RationalRadialTwist) -> "RationalLayerMap":
        return replace(self, twists=(*self.twists, twist))

    def reanchor(self, local_anchor) -> "RationalLayerMap":
        return replace(self, frame=self.frame.reanchor(local_anchor))

    def to_mapping(self) -> dict:
        return {"contract_id": RATIONAL_MAP_CONTRACT_ID,
                "frame": self.frame.to_mapping(),
                "twists": [twist.to_mapping() for twist in self.twists]}

    @classmethod
    def from_mapping(cls, value: dict) -> "RationalLayerMap":
        if value["contract_id"] != RATIONAL_MAP_CONTRACT_ID:
            raise ValueError("unsupported rational layer-map contract")
        return cls(RationalAffine.from_mapping(value["frame"]),
                   tuple(RationalRadialTwist.from_mapping(twist) for twist in value["twists"]))


def relative_layer_maps(source_map: RationalLayerMap,
                        target_map: RationalLayerMap) -> tuple[RationalLayerMap, RationalLayerMap]:
    """Subtract a common world anchor exactly, including every twist center.

    The full rational path is already translation exact. Rebasing is useful
    to reduce common integer magnitudes, with no change of numerical contract.
    Local anchors remain local coordinates and are not translated.
    """
    anchor = target_map.frame.origin

    def rebase(mapping):
        origin = tuple(value-base for value, base in zip(mapping.frame.origin, anchor))
        twists = tuple(replace(twist, center=tuple(value-base for value, base in
                                                   zip(twist.center, anchor)))
                       for twist in mapping.twists)
        return RationalLayerMap(replace(mapping.frame, origin=origin), twists)

    return rebase(source_map), rebase(target_map)
