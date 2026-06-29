from math import isclose

import pytest

from nollm.dream_geometry.geometry.transform import (
    SimilarityTransform,
    TransformWitness,
    apply_transform,
    compose_transforms,
    cycle_residual,
    fit_orientation_preserving_similarity_from_two_pairs,
    invert_transform,
    validate_transform,
)
from nollm.dream_geometry.geometry.types import Vec2


def known_transform() -> SimilarityTransform:
    return SimilarityTransform(0.0, 2.0, Vec2(5.0, -3.0))


def test_dg1_tr_01_two_noncoincident_points_recover_similarity() -> None:
    transform = known_transform()
    recovered = fit_orientation_preserving_similarity_from_two_pairs(Vec2(0, 0), Vec2(1, 0), apply_transform(transform, Vec2(0, 0)), apply_transform(transform, Vec2(1, 0)))
    assert isclose(recovered.a_real, transform.a_real, abs_tol=1e-12)
    assert isclose(recovered.a_imag, transform.a_imag, abs_tol=1e-12)
    assert (recovered.b - transform.b).norm() <= 1e-12


def test_dg1_tr_02_three_consistent_witnesses_verify() -> None:
    transform = known_transform()
    witnesses = tuple(TransformWitness(point, apply_transform(transform, point)) for point in (Vec2(0, 0), Vec2(1, 0), Vec2(0, 1)))
    validation = validate_transform(transform, witnesses, 1.0)
    assert validation.state_recommendation == "verified"
    assert validation.residual.max_residual <= 1e-12


def test_dg1_tr_03_noise_increases_residual() -> None:
    transform = known_transform()
    witnesses = (
        TransformWitness(Vec2(0, 0), apply_transform(transform, Vec2(0, 0))),
        TransformWitness(Vec2(1, 0), apply_transform(transform, Vec2(1, 0))),
        TransformWitness(Vec2(0, 1), apply_transform(transform, Vec2(0, 1)) + Vec2(0.01, 0.0)),
    )
    validation = validate_transform(transform, witnesses, 1.0)
    assert validation.residual.max_residual > 0.0
    assert validation.state_recommendation != "verified"


def test_dg1_tr_04_degenerate_source_pair_rejected() -> None:
    with pytest.raises(ValueError):
        fit_orientation_preserving_similarity_from_two_pairs(Vec2(1, 1), Vec2(1, 1), Vec2(0, 0), Vec2(1, 0))


def test_dg1_tr_05_orientation_reversing_is_rejected() -> None:
    transform = SimilarityTransform(1.0, 0.0, Vec2(0, 0), "orientation_reversing")
    witness = TransformWitness(Vec2(0, 0), Vec2(0, 0))
    assert validate_transform(transform, (witness,), 1.0).state_recommendation == "rejected"


def test_dg1_tr_06_inverse_and_compose_are_identity() -> None:
    transform = known_transform()
    identity = compose_transforms(invert_transform(transform), transform)
    point = Vec2(3.0, -4.0)
    assert (apply_transform(identity, point) - point).norm() <= 1e-12


def test_dg1_tr_07_correct_cycle_residual_is_small() -> None:
    ab = known_transform()
    ba = invert_transform(ab)
    residual = cycle_residual((ab, ba), (Vec2(0, 0), Vec2(1, 1), Vec2(-2, 3)), 1.0)
    assert residual.state_recommendation == "verified"


def test_dg1_tr_08_tampered_cycle_is_not_verified() -> None:
    ab = known_transform()
    bad_ba = SimilarityTransform(0.5, 0.0, Vec2(-2.0, 1.0))
    residual = cycle_residual((ab, bad_ba), (Vec2(0, 0), Vec2(1, 1), Vec2(-2, 3)), 1.0)
    assert residual.state_recommendation == "rejected"


def test_dg1_tr_09_overlap_does_not_create_transform_api() -> None:
    assert fit_orientation_preserving_similarity_from_two_pairs.__name__ != "overlap_to_transform"
