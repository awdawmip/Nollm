from __future__ import annotations

from dataclasses import dataclass

from nollm_core import GeometryAddress


ACTIVE_SEMANTIC_WRITE_POLICY_ID = "nollm_default_dream_layer0_safe_write_v1"
EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID = "nollm_default_dream_multilayer_experiment_write_v1"
ACTIVE_WRITABLE_HEX_RADIUS = (1 << 30) - 1
WRITABLE_FIELD_CONTRACT_ID = "nollm_hex_storage_2p31_writable_2p30_depth2_v1"


class ActiveSemanticWritePolicyError(ValueError):
    def __init__(
        self, address: GeometryAddress, field: str, expected: object, actual: object,
        *, policy_id: str = ACTIVE_SEMANTIC_WRITE_POLICY_ID,
        contract_id: str = WRITABLE_FIELD_CONTRACT_ID,
    ) -> None:
        self.address = address
        self.field = field
        self.expected = expected
        self.actual = actual
        self.policy_id = policy_id
        self.contract_id = contract_id
        super().__init__(
            f"active semantic write rejected {field}={actual!r}; expected {expected!r} "
            f"under {policy_id}"
        )


@dataclass(frozen=True)
class ActiveSemanticWritePolicy:
    """A chosen write scope; layer=None uses GeometryAddress's admitted layers."""

    policy_id: str = ACTIVE_SEMANTIC_WRITE_POLICY_ID
    profile_id: str = "default_dream_v1"
    chart_id: str = "default"
    layer: int | None = 0
    phase: None = None
    active_writable_hex_radius: int = ACTIVE_WRITABLE_HEX_RADIUS
    writable_field_contract_id: str = WRITABLE_FIELD_CONTRACT_ID

    def validate(self, address: object) -> GeometryAddress:
        if type(address) is not GeometryAddress:
            raise TypeError("active semantic write address must be GeometryAddress")
        for field, expected in (
            ("profile_id", self.profile_id),
            ("chart_id", self.chart_id),
            ("layer", self.layer),
            ("phase", self.phase),
        ):
            if field == "layer" and expected is None:
                continue
            actual = getattr(address, field)
            if actual != expected:
                raise ActiveSemanticWritePolicyError(
                    address, field, expected, actual, policy_id=self.policy_id,
                    contract_id=self.writable_field_contract_id,
                )
        required_radius = max(abs(address.q), abs(address.r), abs(address.q + address.r))
        if required_radius > self.active_writable_hex_radius:
            raise ActiveSemanticWritePolicyError(
                address,
                "hex_radius",
                f"<= {self.active_writable_hex_radius}",
                required_radius,
                policy_id=self.policy_id,
                contract_id=self.writable_field_contract_id,
            )
        return address


ACTIVE_SEMANTIC_WRITE_POLICY = ActiveSemanticWritePolicy()

# Explicit experimental write scope. GeometryAddress already validates the
# default profile's physical layer domain; no new geometry/state contract is
# implied by allowing a Host to place evidence in those existing layers.
EXPERIMENTAL_MULTILAYER_WRITE_POLICY = ActiveSemanticWritePolicy(
    policy_id=EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID, layer=None,
)


def semantic_write_policy(policy_id: str) -> ActiveSemanticWritePolicy:
    if policy_id == ACTIVE_SEMANTIC_WRITE_POLICY_ID:
        return ACTIVE_SEMANTIC_WRITE_POLICY
    if policy_id == EXPERIMENTAL_MULTILAYER_WRITE_POLICY_ID:
        return EXPERIMENTAL_MULTILAYER_WRITE_POLICY
    raise ValueError(f"unknown semantic write policy: {policy_id!r}")
