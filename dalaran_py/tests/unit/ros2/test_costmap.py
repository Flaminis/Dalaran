"""Boundary tests for nav2 cost semantics and the costmap palettes."""

from __future__ import annotations

import numpy as np
import pytest
from dalaran.ros2.costmap import (
    COST_INSCRIBED_INFLATED_OBSTACLE,
    COST_LETHAL_OBSTACLE,
    COST_NO_INFORMATION,
    DALARAN_COST_PALETTE,
    RVIZ_COST_PALETTE,
    costmap_to_rgba,
    normalize_cost_values,
    occupancy_byte_to_raw_cost,
    raw_cost_to_occupancy_byte,
)

#: The values a costmap converter has to get exactly right.
BOUNDARIES = [0, 1, 252, 253, 254, 255, -1]


def test_signed_and_unsigned_spellings_normalize_to_the_same_bytes() -> None:
    signed = normalize_cost_values(np.array([-1, 0, 100], dtype=np.int8))
    unsigned = normalize_cost_values(np.array([255, 0, 100], dtype=np.uint8))
    np.testing.assert_array_equal(signed, unsigned)
    assert signed.dtype == np.uint8


def test_python_ints_including_minus_one_normalize() -> None:
    np.testing.assert_array_equal(normalize_cost_values(BOUNDARIES), [0, 1, 252, 253, 254, 255, 255])


def test_raw_costs_translate_onto_the_costmap_2d_publishing_scale() -> None:
    # This is `costmap_2d::Costmap2DPublisher`'s translation table, verbatim.
    np.testing.assert_array_equal(
        raw_cost_to_occupancy_byte([0, 1, 252, 253, 254, 255]),
        [0, 1, 98, 99, 100, 255],
    )


def test_the_published_scale_lifts_back_to_raw_cost_categories() -> None:
    np.testing.assert_array_equal(
        occupancy_byte_to_raw_cost([0, 1, 98, 99, 100, -1]),
        [0, 1, 252, 253, 254, 255],
    )


def test_the_two_scales_round_trip_at_every_boundary() -> None:
    raw = np.array([0, 1, 252, 253, 254, 255], dtype=np.uint8)
    np.testing.assert_array_equal(occupancy_byte_to_raw_cost(raw_cost_to_occupancy_byte(raw)), raw)


def test_the_gradient_never_collides_with_a_reserved_category() -> None:
    # No cost in 1..=252 may translate onto 99 or 100, or the inflation gradient
    # would be indistinguishable from an inscribed or lethal obstacle.
    translated = raw_cost_to_occupancy_byte(np.arange(1, 253, dtype=np.uint8))
    assert translated.max() == 98
    assert translated.min() == 1


def test_reserved_values_get_their_own_colors() -> None:
    rgba = costmap_to_rgba([COST_INSCRIBED_INFLATED_OBSTACLE, COST_LETHAL_OBSTACLE])
    np.testing.assert_array_equal(rgba[0], [*RVIZ_COST_PALETTE.inscribed, 255])
    np.testing.assert_array_equal(rgba[1], [*RVIZ_COST_PALETTE.lethal, 255])


def test_no_reserved_color_ever_appears_on_the_cost_gradient() -> None:
    # The whole point: an inflated-obstacle ring must not look like "cost 200".
    gradient = costmap_to_rgba(np.arange(1, 253, dtype=np.uint8))
    reserved = {RVIZ_COST_PALETTE.inscribed, RVIZ_COST_PALETTE.lethal, RVIZ_COST_PALETTE.unknown}
    seen = {tuple(int(c) for c in pixel[:3]) for pixel in gradient}
    assert seen.isdisjoint(reserved)


def test_the_cost_gradient_is_monotonic_between_its_endpoints() -> None:
    gradient = costmap_to_rgba(np.arange(1, 253, dtype=np.uint8)).astype(np.int32)
    np.testing.assert_array_equal(gradient[0, :3], RVIZ_COST_PALETTE.low)
    np.testing.assert_array_equal(gradient[-1, :3], RVIZ_COST_PALETTE.high)
    assert np.all(np.diff(gradient[:, 0]) >= 0)  # red rises
    assert np.all(np.diff(gradient[:, 2]) <= 0)  # blue falls


def test_free_and_unknown_are_transparent_so_layers_show_through() -> None:
    rgba = costmap_to_rgba([0, COST_NO_INFORMATION, 1])
    assert rgba[0, 3] == 0
    assert rgba[1, 3] == 0
    assert rgba[2, 3] == 255


def test_the_signed_minus_one_spelling_is_unknown_not_maximum_cost() -> None:
    signed = costmap_to_rgba(np.array([-1], dtype=np.int8))
    np.testing.assert_array_equal(signed, costmap_to_rgba([COST_NO_INFORMATION]))


def test_the_occupancy_scale_reads_ninety_nine_as_inscribed_not_as_high_cost() -> None:
    rgba = costmap_to_rgba([98, 99, 100], scale="occupancy")
    np.testing.assert_array_equal(rgba[1][:3], RVIZ_COST_PALETTE.inscribed)
    np.testing.assert_array_equal(rgba[2][:3], RVIZ_COST_PALETTE.lethal)
    # 98 is still on the gradient, at its far end.
    np.testing.assert_array_equal(rgba[0][:3], RVIZ_COST_PALETTE.high)


def test_the_dalaran_palette_keeps_the_same_semantics_with_different_hues() -> None:
    rgba = costmap_to_rgba([0, 1, 253, 254, 255], palette=DALARAN_COST_PALETTE)
    np.testing.assert_array_equal(rgba[2][:3], DALARAN_COST_PALETTE.inscribed)
    np.testing.assert_array_equal(rgba[3][:3], DALARAN_COST_PALETTE.lethal)
    assert rgba[0, 3] == 0
    assert rgba[4, 3] == 0


def test_shape_is_preserved_with_a_trailing_rgba_axis() -> None:
    rgba = costmap_to_rgba(np.zeros((3, 4), dtype=np.uint8))
    assert rgba.shape == (3, 4, 4)


def test_an_unknown_scale_is_rejected() -> None:
    with pytest.raises(ValueError, match="scale"):
        costmap_to_rgba([0], scale="probability")  # type: ignore[arg-type]
