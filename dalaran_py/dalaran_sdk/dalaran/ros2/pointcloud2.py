"""
A dependency-free `sensor_msgs/PointCloud2` decoder.

ROS 2 ships point clouds as an opaque byte blob plus a description of how the
bytes are laid out. Every driver picks a different layout: Velodyne adds `ring`
and `time`, Ouster adds `t`/`reflectivity`/`ambient`, Livox emits `tag`/`line`,
and RGB-D cameras pack colors into a `float32` field. Rather than special-casing
drivers, this module builds a numpy structured dtype straight from the message's
own `fields`/`point_step` description and takes a zero-copy view over the buffer.

Everything here is a pure function over plain buffers and duck-typed message
objects: nothing in this module imports `rclpy`, `sensor_msgs` or `dalaran`, so
it can be unit tested (and used offline on rosbag data) without ROS installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence

    import numpy.typing as npt

__all__ = [
    "DATATYPE_NAMES",
    "DecodedCloud",
    "PointField",
    "decode_pointcloud2",
    "fields_to_dtype",
    "read_points",
    "unpack_rgb",
]

# `sensor_msgs/PointField` datatype constants -> numpy scalar types.
DATATYPE_NAMES: dict[int, str] = {
    1: "i1",  # INT8
    2: "u1",  # UINT8
    3: "i2",  # INT16
    4: "u2",  # UINT16
    5: "i4",  # INT32
    6: "u4",  # UINT32
    7: "f4",  # FLOAT32
    8: "f8",  # FLOAT64
}

#: Field names drivers use for a per-point return strength.
INTENSITY_FIELDS = ("intensity", "reflectivity", "reflectance", "i")
#: Field names drivers use for the laser/scan-line index.
RING_FIELDS = ("ring", "line", "channel", "laser_id")
#: Field names drivers use for a per-point time offset within the sweep.
TIME_FIELDS = ("t", "time", "timestamp", "time_offset", "time_stamp")


@dataclass(frozen=True)
class PointField:
    """
    A plain-data stand-in for `sensor_msgs/PointField`.

    Real ROS messages are accepted anywhere a `PointField` is; this class exists
    so that tests and offline tooling can describe a layout without ROS.

    Examples
    --------
    ```python
    from dalaran.ros2.pointcloud2 import PointField

    xyz = [
        PointField(name="x", offset=0, datatype=7, count=1),
        PointField(name="y", offset=4, datatype=7, count=1),
        PointField(name="z", offset=8, datatype=7, count=1),
    ]
    assert xyz[2].offset == 8
    ```

    """

    name: str
    offset: int
    datatype: int
    count: int = 1


@dataclass
class DecodedCloud:
    """
    The result of decoding a `sensor_msgs/PointCloud2`.

    Attributes
    ----------
    positions:
        `(N, 3)` float32 xyz positions in the cloud's own frame.
    intensity:
        `(N,)` float32 return strength, or `None` if the driver did not send one.
    colors:
        `(N, 3)` uint8 RGB colors unpacked from a packed `rgb`/`rgba` field, or
        from separate `r`/`g`/`b` fields. `None` when the cloud has no color.
    ring:
        `(N,)` int32 laser/scan-line index, or `None`.
    times:
        `(N,)` float64 per-point time offsets in seconds relative to the message
        stamp, or `None`. Integer nanosecond fields are converted for you.
    frame_id:
        The `header.frame_id` the cloud was expressed in, when known.
    field_names:
        Every field name present in the original message, in offset order.

    """

    positions: npt.NDArray[np.float32]
    intensity: npt.NDArray[np.float32] | None = None
    colors: npt.NDArray[np.uint8] | None = None
    ring: npt.NDArray[np.int32] | None = None
    times: npt.NDArray[np.float64] | None = None
    frame_id: str = ""
    field_names: list[str] = dataclass_field(default_factory=list)

    def __len__(self) -> int:
        return int(self.positions.shape[0])


def _field_tuple(field: Any) -> tuple[str, int, int, int]:
    count = int(getattr(field, "count", 1) or 1)
    return (str(field.name), int(field.offset), int(field.datatype), count)


def fields_to_dtype(
    fields: Sequence[Any],
    point_step: int,
    *,
    is_bigendian: bool = False,
) -> np.dtype[Any]:
    """
    Build the numpy structured dtype that describes one point.

    Padding between fields is expressed through explicit offsets and an itemsize
    of `point_step`, so trailing or interleaved padding bytes (which most drivers
    emit to keep points 16-byte aligned) cost nothing and are never copied.

    Parameters
    ----------
    fields:
        The message's `fields`, or any objects with `name`, `offset`, `datatype`
        and `count` attributes.
    point_step:
        Length of one point in bytes, i.e. the message's `point_step`.
    is_bigendian:
        Whether the sender serialized in big-endian byte order.

    Returns
    -------
    numpy.dtype
        A structured dtype with `itemsize == point_step`.

    Examples
    --------
    ```python
    from dalaran.ros2.pointcloud2 import PointField, fields_to_dtype

    dtype = fields_to_dtype(
        [PointField(name="x", offset=0, datatype=7), PointField(name="y", offset=4, datatype=7)],
        point_step=16,
    )
    assert dtype.itemsize == 16
    assert dtype.names == ("x", "y")
    ```

    """
    order = ">" if is_bigendian else "<"
    names: list[str] = []
    formats: list[Any] = []
    offsets: list[int] = []

    seen: dict[str, int] = {}
    for raw in sorted((_field_tuple(f) for f in fields), key=lambda f: f[1]):
        name, offset, datatype, count = raw
        if count <= 0:
            continue
        try:
            scalar = DATATYPE_NAMES[datatype]
        except KeyError:
            msg = f"Unsupported sensor_msgs/PointField datatype {datatype} for field {name!r}"
            raise ValueError(msg) from None

        # Some bags contain duplicated field names; keep them all, disambiguated.
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 0

        fmt: Any = f"{order}{scalar}"
        if count > 1:
            fmt = (fmt, (count,))

        names.append(name)
        formats.append(fmt)
        offsets.append(offset)

    if not names:
        msg = "sensor_msgs/PointCloud2 has no usable fields"
        raise ValueError(msg)

    itemsize = int(point_step)
    end = max(off + np.dtype(fmt).itemsize for off, fmt in zip(offsets, formats, strict=False))
    if itemsize < end:
        msg = f"point_step ({itemsize}) is smaller than the fields it must hold ({end} bytes)"
        raise ValueError(msg)

    return np.dtype({"names": names, "formats": formats, "offsets": offsets, "itemsize": itemsize})


def read_points(
    data: Any,
    fields: Sequence[Any],
    *,
    width: int,
    height: int = 1,
    point_step: int,
    row_step: int | None = None,
    is_bigendian: bool = False,
    is_dense: bool = True,
    organized: bool = False,
) -> npt.NDArray[Any]:
    """
    View a raw `sensor_msgs/PointCloud2` buffer as a numpy structured array.

    The common case (`row_step == width * point_step`, native byte order) is a
    pure view: no bytes are copied. Padded rows are compacted first, which is the
    only case that needs a copy.

    Parameters
    ----------
    data:
        The message's `data`, as `bytes`, `bytearray`, `memoryview` or a numpy
        `uint8` array.
    fields:
        The message's `fields`.
    width:
        Points per row.
    height:
        Number of rows. `1` for unorganized clouds.
    point_step:
        Bytes per point.
    row_step:
        Bytes per row. Defaults to `width * point_step`.
    is_bigendian:
        Whether the sender serialized in big-endian byte order.
    is_dense:
        When `False`, points with a non-finite `x`, `y` or `z` are dropped, as
        the `sensor_msgs/PointCloud2` contract requires. Ignored when the cloud
        is returned organized.
    organized:
        Return a `(height, width)` array instead of a flat `(height * width,)`
        one. Useful for RGB-D clouds where the 2D structure is meaningful.

    Returns
    -------
    numpy.ndarray
        A structured array whose fields are named after the message's fields.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.pointcloud2 import PointField, read_points

    fields = [
        PointField(name="x", offset=0, datatype=7),
        PointField(name="y", offset=4, datatype=7),
        PointField(name="z", offset=8, datatype=7),
    ]
    raw = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32).tobytes()
    points = read_points(raw, fields, width=2, point_step=12)
    np.testing.assert_allclose(points["y"], [2.0, 5.0])
    ```

    """
    width = int(width)
    height = int(height)
    point_step = int(point_step)
    if width < 0 or height < 0:
        msg = "PointCloud2 width and height must be non-negative"
        raise ValueError(msg)
    if point_step <= 0:
        msg = "PointCloud2 point_step must be positive"
        raise ValueError(msg)

    dtype = fields_to_dtype(fields, point_step, is_bigendian=is_bigendian)
    row_step = width * point_step if row_step is None else int(row_step)

    buffer = np.frombuffer(memoryview(data).cast("B"), dtype=np.uint8)

    needed = height * row_step
    if buffer.size < needed:
        msg = f"PointCloud2 data is {buffer.size} bytes, but height * row_step is {needed}"
        raise ValueError(msg)

    if row_step != width * point_step:
        # Rows are padded; compact them before viewing.
        rows = buffer[:needed].reshape(height, row_step)[:, : width * point_step]
        buffer = np.ascontiguousarray(rows).reshape(-1)
    else:
        buffer = buffer[:needed]

    points = buffer.view(dtype).reshape(height, width)

    if organized:
        return points

    points = points.reshape(-1)  # type: ignore[assignment]  # 2-D -> 1-D view
    if not is_dense and {"x", "y", "z"} <= set(dtype.names or ()):
        finite = np.isfinite(points["x"]) & np.isfinite(points["y"]) & np.isfinite(points["z"])
        if not finite.all():
            points = points[finite]
    return points


def unpack_rgb(packed: npt.ArrayLike) -> npt.NDArray[np.uint8]:
    """
    Unpack ROS's packed color field into `(N, 3)` uint8 RGB.

    ROS stores colors as `0x00RRGGBB` in a 32-bit slot that drivers declare as
    either `UINT32` or - historically, and still very common - `FLOAT32`. Both
    are handled: float input is reinterpreted bit-for-bit rather than rounded.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.pointcloud2 import unpack_rgb

    colors = unpack_rgb(np.array([0x00FF8000], dtype=np.uint32))
    np.testing.assert_array_equal(colors, [[255, 128, 0]])
    ```

    """
    values = np.asarray(packed)
    if values.dtype.kind == "f":
        values = values.astype(values.dtype.newbyteorder("="), copy=False)
        values = values.view(np.uint32 if values.dtype.itemsize == 4 else np.uint64)
    integers = values.astype(np.uint32, copy=False).reshape(-1)

    out = np.empty((integers.shape[0], 3), dtype=np.uint8)
    out[:, 0] = (integers >> 16) & 0xFF
    out[:, 1] = (integers >> 8) & 0xFF
    out[:, 2] = integers & 0xFF
    return out


def _first_field(names: Sequence[str], candidates: Sequence[str]) -> str | None:
    lowered = {name.lower(): name for name in names}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    return None


def _to_seconds(values: npt.NDArray[Any]) -> npt.NDArray[np.float64]:
    """Normalize a per-point time field to seconds."""
    if values.dtype.kind in "iu":
        # Integer time fields are nanoseconds since the sweep start (Ouster,
        # Velodyne's `t`); floats are already seconds (Velodyne's `time`).
        return values.astype(np.float64) * 1e-9
    return values.astype(np.float64)


def decode_pointcloud2(msg: Any) -> DecodedCloud:
    """
    Decode a `sensor_msgs/PointCloud2` into arrays Dalaran can log directly.

    This is the driver-agnostic entry point: it picks up `x`/`y`/`z` plus
    whichever of `intensity`, `rgb`, `ring` and `t` the sender happened to
    include, so Velodyne, Ouster, Livox and RGB-D clouds all work unchanged.

    Parameters
    ----------
    msg:
        Anything with the `sensor_msgs/PointCloud2` attributes: `data`, `fields`,
        `width`, `height`, `point_step`, `row_step`, `is_bigendian`, `is_dense`
        and optionally `header`.

    Returns
    -------
    DecodedCloud
        Positions plus whichever optional channels were present.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.ros2.pointcloud2 import PointField, decode_pointcloud2


    class FakeCloud:
        fields = [
            PointField(name="x", offset=0, datatype=7),
            PointField(name="y", offset=4, datatype=7),
            PointField(name="z", offset=8, datatype=7),
        ]
        width, height, point_step, row_step = 2, 1, 12, 24
        is_bigendian, is_dense = False, True
        data = np.arange(6, dtype=np.float32).tobytes()


    cloud = decode_pointcloud2(FakeCloud())
    np.testing.assert_allclose(cloud.positions[1], [3.0, 4.0, 5.0])
    ```

    """
    points = read_points(
        msg.data,
        msg.fields,
        width=msg.width,
        height=getattr(msg, "height", 1),
        point_step=msg.point_step,
        row_step=getattr(msg, "row_step", None),
        is_bigendian=bool(getattr(msg, "is_bigendian", False)),
        is_dense=bool(getattr(msg, "is_dense", True)),
    )

    names = list(points.dtype.names or ())
    missing = {"x", "y", "z"} - set(names)
    if missing:
        msg_text = f"PointCloud2 is missing the {sorted(missing)} field(s); got {names}"
        raise ValueError(msg_text)

    positions = np.empty((points.shape[0], 3), dtype=np.float32)
    for index, axis in enumerate("xyz"):
        positions[:, index] = points[axis].astype(np.float32, copy=False)

    intensity = None
    intensity_name = _first_field(names, INTENSITY_FIELDS)
    if intensity_name is not None:
        intensity = np.ascontiguousarray(points[intensity_name], dtype=np.float32)

    colors = None
    color_name = _first_field(names, ("rgb", "rgba"))
    if color_name is not None:
        colors = unpack_rgb(points[color_name])
    elif {"r", "g", "b"} <= set(names):
        colors = np.stack([points["r"], points["g"], points["b"]], axis=-1).astype(np.uint8)

    ring = None
    ring_name = _first_field(names, RING_FIELDS)
    if ring_name is not None:
        ring = np.ascontiguousarray(points[ring_name], dtype=np.int32)

    times = None
    time_name = _first_field(names, TIME_FIELDS)
    if time_name is not None:
        times = _to_seconds(np.ascontiguousarray(points[time_name]))

    header = getattr(msg, "header", None)
    frame_id = str(getattr(header, "frame_id", "") or "")

    return DecodedCloud(
        positions=positions,
        intensity=intensity,
        colors=colors,
        ring=ring,
        times=times,
        frame_id=frame_id,
        field_names=names,
    )
