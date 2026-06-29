"""DG2 internal gravity snapshot calculation."""

from math import log

from nollm.dream_geometry.geometry.hexgrid import hex_distance
from nollm.dream_geometry.protocol.contracts import CoverState

from .types import GravityContribution, GravityPolicy, GravitySnapshot, cell_ref_key, float_token, stable_id


def calculate_gravity_snapshot(covers, policy: GravityPolicy = GravityPolicy()) -> GravitySnapshot:
    _reject_duplicate_cover_ids(covers)
    active = tuple(sorted((cover for cover in covers if cover.state in {CoverState.stable, CoverState.crystallized}), key=lambda cover: cover.cover_id))
    if not active:
        return GravitySnapshot(stable_id("gravity_snapshot:v2", {"covers": (), "policy": policy.version}), None, (), (), policy.policy_id, policy.version)
    fingerprints = {cover.chart_fingerprint for cover in active}
    if len(fingerprints) != 1:
        raise ValueError("gravity snapshot requires one chart fingerprint")
    contributions = tuple(_contribution(cover, active, policy) for cover in active)
    payload = {
        "covers": tuple(cover.cover_id for cover in active),
        "policy_id": policy.policy_id,
        "policy_version": policy.version,
        "potentials": tuple(float_token(item.potential) for item in contributions),
    }
    return GravitySnapshot(stable_id("gravity_snapshot:v2", payload), active[0].chart_fingerprint, contributions, tuple(cover.cover_id for cover in active), policy.policy_id, policy.version)


def _contribution(cover, covers, policy: GravityPolicy) -> GravityContribution:
    congestion = sum(1 for other in covers if other.cover_id != cover.cover_id and hex_distance(cover.support_cell.axial, other.support_cell.axial) <= 1)
    stability_term = min(1.0, cover.stability / policy.stability_epoch_scale)
    support_term = (
        policy.mass_weight * log(1.0 + cover.mass)
        + policy.support_weight * log(1.0 + len(cover.support_keys))
        + policy.axis_weight * max(0, len(cover.axes_present) - 1)
        + policy.stability_weight * stability_term
    )
    penalties = (
        ("genericity", policy.genericity_penalty_weight * cover.genericity),
        ("ambiguity", policy.ambiguity_penalty_weight * cover.ambiguity),
        ("conflict", policy.conflict_penalty_weight * cover.conflict),
        ("congestion", policy.congestion_penalty_weight * log(1.0 + congestion)),
    )
    potential = support_term - sum(value for _, value in penalties)
    return GravityContribution(cover.cover_id, f"{cover.support_cell.chart_id}:{cover.support_cell.axial.q}:{cover.support_cell.axial.r}", potential, support_term, penalties, policy.policy_id)


def _reject_duplicate_cover_ids(covers) -> None:
    seen: set[str] = set()
    for cover in covers:
        if cover.cover_id in seen:
            raise ValueError("duplicate cover_id")
        seen.add(cover.cover_id)
