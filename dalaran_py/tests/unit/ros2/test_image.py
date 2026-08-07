"""Unit tests for `sensor_msgs/Image` and `sensor_msgs/CompressedImage` decoding."""

from __future__ import annotations

import numpy as np
import pytest
from dalaran.ros2.image import compressed_image_media_type, decode_image


def test_rgb8_is_passed_through() -> None:
    decoded = decode_image(bytes([10, 20, 30, 40, 50, 60]), width=2, height=1, encoding="rgb8")
    np.testing.assert_array_equal(decoded.array, [[[10, 20, 30], [40, 50, 60]]])
    assert decoded.kind == "color"
    assert decoded.depth_meter is None


def test_bgr8_swaps_the_color_channels() -> None:
    decoded = decode_image(bytes([255, 0, 0]), width=1, height=1, encoding="bgr8")
    np.testing.assert_array_equal(decoded.array[0, 0], [0, 0, 255])


def test_bgra8_swaps_color_but_keeps_alpha_last() -> None:
    decoded = decode_image(bytes([1, 2, 3, 4]), width=1, height=1, encoding="bgra8")
    np.testing.assert_array_equal(decoded.array[0, 0], [3, 2, 1, 4])


def test_mono8_stays_two_dimensional() -> None:
    decoded = decode_image(bytes([1, 2, 3, 4]), width=2, height=2, encoding="mono8")
    assert decoded.array.shape == (2, 2)
    assert decoded.kind == "mono"


def test_16uc1_is_depth_in_millimeters() -> None:
    raw = np.array([[1000, 2000]], dtype="<u2").tobytes()
    decoded = decode_image(raw, width=2, height=1, encoding="16UC1")
    assert decoded.kind == "depth"
    assert decoded.depth_meter == 1000.0
    np.testing.assert_array_equal(decoded.array, [[1000, 2000]])


def test_32fc1_is_depth_in_meters() -> None:
    raw = np.array([[1.5, 2.5]], dtype="<f4").tobytes()
    decoded = decode_image(raw, width=2, height=1, encoding="32FC1")
    assert decoded.kind == "depth"
    assert decoded.depth_meter == 1.0
    np.testing.assert_allclose(decoded.array, [[1.5, 2.5]])


def test_mono16_is_an_image_not_a_depth_map() -> None:
    raw = np.array([[7, 8]], dtype="<u2").tobytes()
    decoded = decode_image(raw, width=2, height=1, encoding="mono16")
    assert decoded.kind == "mono"
    assert decoded.depth_meter is None


def test_8uc3_is_treated_as_color() -> None:
    decoded = decode_image(bytes(range(6)), width=2, height=1, encoding="8UC3")
    assert decoded.kind == "color"
    assert decoded.array.shape == (1, 2, 3)


def test_padded_rows_are_cropped_back_to_the_image() -> None:
    # A 2x2 RGB image whose publisher padded each row out to 8 bytes.
    rows = b"".join(bytes([r * 6 + i for i in range(6)]) + b"\xff\xff" for r in range(2))
    decoded = decode_image(rows, width=2, height=2, encoding="rgb8", step=8)
    np.testing.assert_array_equal(decoded.array[0, 0], [0, 1, 2])
    np.testing.assert_array_equal(decoded.array[1, 1], [9, 10, 11])


def test_big_endian_pixels_are_byteswapped() -> None:
    raw = np.array([[4096]], dtype=">u2").tobytes()
    decoded = decode_image(raw, width=1, height=1, encoding="mono16", is_bigendian=True)
    assert int(decoded.array[0, 0]) == 4096


def test_a_step_smaller_than_a_row_is_rejected() -> None:
    with pytest.raises(ValueError, match="step"):
        decode_image(bytes(6), width=2, height=1, encoding="rgb8", step=4)


def test_a_short_buffer_is_rejected() -> None:
    with pytest.raises(ValueError, match="bytes"):
        decode_image(bytes(3), width=2, height=1, encoding="rgb8")


def test_bayer_encodings_show_the_raw_sensor_plane() -> None:
    decoded = decode_image(bytes([1, 2, 3, 4]), width=2, height=2, encoding="bayer_rggb8")
    assert decoded.kind == "mono"
    assert decoded.array.shape == (2, 2)


def test_unknown_encodings_are_rejected_loudly() -> None:
    with pytest.raises(ValueError, match="encoding"):
        decode_image(b"", width=0, height=0, encoding="yuv422_but_not_really")


@pytest.mark.parametrize(
    ("format_string", "media_type"),
    [
        ("rgb8; jpeg compressed bgr8", "image/jpeg"),
        ("bgr8; png compressed bgr8", "image/png"),
        ("jpg", "image/jpeg"),
        ("webp", "image/webp"),
    ],
)
def test_compressed_formats_map_onto_media_types(format_string: str, media_type: str) -> None:
    assert compressed_image_media_type(format_string) == media_type


def test_unknown_compressed_formats_are_rejected() -> None:
    with pytest.raises(ValueError, match="format"):
        compressed_image_media_type("some_bespoke_codec")
