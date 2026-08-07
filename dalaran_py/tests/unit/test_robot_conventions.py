from __future__ import annotations

import numpy as np
import pytest
from dalaran.robot import conventions
from dalaran.robot.conventions import FLU, FRD, RDF, RUB, convention_matrix, convert_frame_convention

ALL = [FLU, RDF, FRD, RUB]


@pytest.mark.parametrize("src", ALL)
@pytest.mark.parametrize("dst", ALL)
def test_conversions_are_rotations(src: str, dst: str) -> None:
    m = convention_matrix(src, dst)
    np.testing.assert_allclose(m @ m.T, np.eye(3), atol=1e-12)
    assert np.linalg.det(m) == pytest.approx(1.0)


@pytest.mark.parametrize("src", ALL)
@pytest.mark.parametrize("dst", ALL)
def test_conversions_are_invertible(src: str, dst: str) -> None:
    np.testing.assert_allclose(
        convention_matrix(dst, src),
        convention_matrix(src, dst).T,
        atol=1e-12,
    )


def test_identity_conversion() -> None:
    np.testing.assert_allclose(convention_matrix(FLU, FLU), np.eye(3), atol=1e-12)


def test_flu_to_rdf_is_the_optical_rotation() -> None:
    m = convention_matrix(FLU, RDF)
    # forward -> +z, left -> -x, up -> -y
    np.testing.assert_allclose(m @ [1, 0, 0], [0, 0, 1], atol=1e-12)
    np.testing.assert_allclose(m @ [0, 1, 0], [-1, 0, 0], atol=1e-12)
    np.testing.assert_allclose(m @ [0, 0, 1], [0, -1, 0], atol=1e-12)


def test_flu_to_frd_flips_y_and_z() -> None:
    np.testing.assert_allclose(
        convention_matrix(FLU, FRD),
        np.diag([1.0, -1.0, -1.0]),
        atol=1e-12,
    )


def test_rdf_to_rub_flips_y_and_z() -> None:
    np.testing.assert_allclose(
        convention_matrix(RDF, RUB),
        np.diag([1.0, -1.0, -1.0]),
        atol=1e-12,
    )


def test_convert_points() -> None:
    flu = np.array([[2.0, 1.0, 0.0], [0.0, 0.0, 3.0]])
    rdf = convert_frame_convention(flu, FLU, RDF)
    np.testing.assert_allclose(rdf, [[-1.0, 0.0, 2.0], [0.0, -3.0, 0.0]], atol=1e-12)
    np.testing.assert_allclose(convert_frame_convention(rdf, RDF, FLU), flu, atol=1e-12)


def test_convert_preserves_lengths_and_shape() -> None:
    rng = np.random.default_rng(0)
    points = rng.normal(size=(4, 5, 3))
    converted = convert_frame_convention(points, FLU, RDF)
    assert converted.shape == points.shape
    np.testing.assert_allclose(
        np.linalg.norm(converted, axis=-1),
        np.linalg.norm(points, axis=-1),
        atol=1e-12,
    )


def test_convert_transform_is_a_similarity() -> None:
    from dalaran.robot._math import euler_to_matrix, make_matrix, transform_points

    t_flu = make_matrix(translation=[1.0, 2.0, 3.0], rotation=euler_to_matrix([0.2, -0.3, 0.9]))
    t_rdf = convert_frame_convention(t_flu, FLU, RDF)

    point_flu = np.array([[0.4, -0.2, 0.7]])
    # Transforming then converting must equal converting then transforming.
    np.testing.assert_allclose(
        convert_frame_convention(transform_points(t_flu, point_flu), FLU, RDF),
        transform_points(t_rdf, convert_frame_convention(point_flu, FLU, RDF)),
        atol=1e-12,
    )


def test_invalid_conventions_are_rejected() -> None:
    with pytest.raises(ValueError, match="exactly 3 letters"):
        convention_matrix("FL", FLU)
    with pytest.raises(ValueError, match="Unknown axis letter"):
        convention_matrix("XYZ", FLU)
    with pytest.raises(ValueError, match="degenerate"):
        convention_matrix("FLB", FLU)
    with pytest.raises(ValueError, match="left-handed"):
        convention_matrix("FLD", FLU)


def test_conventions_are_case_insensitive() -> None:
    np.testing.assert_allclose(convention_matrix("flu", "rdf"), convention_matrix(FLU, RDF))


def test_module_constants() -> None:
    assert (conventions.FLU, conventions.RDF, conventions.FRD, conventions.RUB) == ("FLU", "RDF", "FRD", "RUB")


def test_bad_shape_is_rejected() -> None:
    with pytest.raises(ValueError, match="trailing dimension of 3"):
        convert_frame_convention(np.zeros((2, 4)), FLU, RDF)
