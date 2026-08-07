"""
Pure decoding of `sensor_msgs/Image` and `sensor_msgs/CompressedImage` payloads.

ROS image messages are a raw buffer plus an encoding string, and the encoding
string is where the ambiguity lives: `bgr8` needs its channels swapped, `16UC1`
is almost always a depth image in millimeters, `32FC1` is a depth image in
meters, and `step` may be larger than `width * pixel_size` because the publisher
padded its rows. This module resolves all of that into a plain numpy array plus
a semantic hint, without importing `cv_bridge`, OpenCV or ROS.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

if TYPE_CHECKING:
    import numpy.typing as npt

__all__ = [
    "DecodedImage",
    "compressed_image_media_type",
    "decode_image",
]

ImageKind = Literal["color", "mono", "depth"]

# `encoding` -> (numpy scalar type, channel count, channel order, semantic kind).
_NAMED_ENCODINGS: dict[str, tuple[str, int, str, ImageKind]] = {
    "mono8": ("u1", 1, "rgb", "mono"),
    "mono16": ("u2", 1, "rgb", "mono"),
    "rgb8": ("u1", 3, "rgb", "color"),
    "rgba8": ("u1", 4, "rgb", "color"),
    "bgr8": ("u1", 3, "bgr", "color"),
    "bgra8": ("u1", 4, "bgr", "color"),
    "rgb16": ("u2", 3, "rgb", "color"),
    "rgba16": ("u2", 4, "rgb", "color"),
    "bgr16": ("u2", 3, "bgr", "color"),
    "bgra16": ("u2", 4, "bgr", "color"),
}

# OpenCV-style `<bits><type>C<channels>` encodings, e.g. `32FC1` or `8UC3`.
_CV_ENCODING = re.compile(r"^(8|16|32|64)(U|S|F)C?(\d+)?$", re.IGNORECASE)
_CV_SCALARS = {
    ("8", "u"): "u1",
    ("8", "s"): "i1",
    ("16", "u"): "u2",
    ("16", "s"): "i2",
    ("32", "s"): "i4",
    ("32", "f"): "f4",
    ("64", "f"): "f8",
}


@dataclass
class DecodedImage:
    """
    A decoded `sensor_msgs/Image`.

    Attributes
    ----------
    array:
        `(H, W)` or `(H, W, C)` numpy array with channels already in RGB order.
    kind:
        `"color"`, `"mono"` or `"depth"`, i.e. which Dalaran archetype this
        should become.
    encoding:
        The original ROS encoding string.
    depth_meter:
        For depth images, how many stored units make up one meter: `1000` for the
        `16UC1` millimeter convention, `1.0` for `32FC1`. `None` otherwise.

    """

    array: npt.NDArray[Any]
    kind: ImageKind
    encoding: str
    depth_meter: float | None = None


def _resolve_encoding(encoding: str) -> tuple[str, int, str, ImageKind, float | None]:
    key = encoding.strip().lower()
    if key in _NAMED_ENCODINGS:
        scalar, channels, order, kind = _NAMED_ENCODINGS[key]
        return scalar, channels, order, kind, None

    match = _CV_ENCODING.match(key)
    if match is not None:
        bits, letter, channels_text = match.groups()
        try:
            scalar = _CV_SCALARS[(bits, letter.lower())]
        except KeyError:
            msg = f"Unsupported sensor_msgs/Image encoding {encoding!r}"
            raise ValueError(msg) from None
        channels = int(channels_text or 1)
        if channels == 1 and letter.lower() == "f":
            # `32FC1`/`64FC1` single channel floats are depth images in meters.
            return scalar, 1, "rgb", "depth", 1.0
        if channels == 1 and (bits, letter.lower()) == ("16", "u"):
            # `16UC1` is the ROS depth convention: millimeters.
            return scalar, 1, "rgb", "depth", 1000.0
        kind = "mono" if channels == 1 else "color"
        return scalar, channels, "rgb", kind, None

    if key.startswith("bayer_"):
        # Debayering needs a real ISP; show the raw sensor plane instead of lying.
        return "u1", 1, "rgb", "mono", None

    msg = f"Unsupported sensor_msgs/Image encoding {encoding!r}"
    raise ValueError(msg)


def decode_image(
    data: Any,
    *,
    width: int,
    height: int,
    encoding: str,
    step: int | None = None,
    is_bigendian: bool = False,
) -> DecodedImage:
    """
    Decode a raw `sensor_msgs/Image` buffer into a numpy array.

    Rows longer than `width * pixel_size` are cropped back to the image, BGR
    encodings are swapped into RGB, and single-channel float or `16UC1` images
    are reported as depth so the caller can log a [`dalaran.DepthImage`][] with
    the right `meter` scale instead of a meaningless grayscale image.

    Parameters
    ----------
    data:
        The message's `data`.
    width:
        Image width in pixels.
    height:
        Image height in pixels.
    encoding:
        The message's `encoding` string, e.g. `"bgr8"`, `"mono16"` or `"32FC1"`.
    step:
        Bytes per row. Defaults to `width * pixel_size`.
    is_bigendian:
        Whether the sender serialized in big-endian byte order.

    Returns
    -------
    DecodedImage
        The pixel array plus how it should be interpreted.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.image import decode_image

    # A single blue pixel, published as BGR.
    decoded = decode_image(bytes([255, 0, 0]), width=1, height=1, encoding="bgr8")
    np.testing.assert_array_equal(decoded.array[0, 0], [0, 0, 255])
    assert decoded.kind == "color"
    ```

    """
    width = int(width)
    height = int(height)
    scalar, channels, order, kind, depth_meter = _resolve_encoding(encoding)

    dtype = np.dtype((">" if is_bigendian else "<") + scalar)
    pixel_size = dtype.itemsize * channels
    row_size = width * pixel_size
    step = row_size if step is None else int(step)
    if step < row_size:
        msg = f"sensor_msgs/Image step ({step}) is smaller than one row of {encoding} pixels ({row_size})"
        raise ValueError(msg)

    buffer = np.frombuffer(memoryview(data).cast("B"), dtype=np.uint8)
    needed = height * step
    if buffer.size < needed:
        msg = f"sensor_msgs/Image data is {buffer.size} bytes but height * step is {needed}"
        raise ValueError(msg)

    rows = buffer[:needed].reshape(height, step)[:, :row_size]
    array = np.ascontiguousarray(rows).view(dtype)
    array = array.reshape(height, width, channels) if channels > 1 else array.reshape(height, width)

    if order == "bgr":
        # Reverse the color channels but keep alpha last.
        if channels == 4:
            array = np.concatenate([array[..., 2::-1], array[..., 3:]], axis=-1)
        else:
            array = array[..., ::-1]
        array = np.ascontiguousarray(array)

    return DecodedImage(array=array, kind=kind, encoding=encoding, depth_meter=depth_meter)


def compressed_image_media_type(format_string: str) -> str:
    """
    Map a `sensor_msgs/CompressedImage.format` string onto an IANA media type.

    ROS format strings are free-form and usually look like `"rgb8; jpeg
    compressed bgr8"`, so this looks for the codec name anywhere in the string.

    Examples
    --------
    ```python
    from dalaran.ros2.image import compressed_image_media_type

    assert compressed_image_media_type("rgb8; jpeg compressed bgr8") == "image/jpeg"
    assert compressed_image_media_type("png") == "image/png"
    ```

    """
    lowered = format_string.lower()
    for needle, media_type in (
        ("jpeg", "image/jpeg"),
        ("jpg", "image/jpeg"),
        ("png", "image/png"),
        ("webp", "image/webp"),
        ("avif", "image/avif"),
        ("tiff", "image/tiff"),
    ):
        if needle in lowered:
            return media_type
    msg = f"Unsupported sensor_msgs/CompressedImage format {format_string!r}"
    raise ValueError(msg)
