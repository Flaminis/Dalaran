"""Unit tests for the dependency-free `sensor_msgs/PointCloud2` decoder."""

from __future__ import annotations

import numpy as np
import pytest
from dalaran.ros2.pointcloud2 import (
    PointField,
    decode_pointcloud2,
    fields_to_dtype,
    read_points,
    unpack_rgb,
)

FLOAT32 = 7
UINT32 = 6
UINT16 = 4
UINT8 = 2


class FakeHeader:
    def __init__(self, frame_id: str = "") -> None:
        self.frame_id = frame_id


class FakeCloud:
    """A synthetic `sensor_msgs/PointCloud2` built straight from a numpy buffer."""

    def __init__(
        self,
        record: np.ndarray,
        fields: list[PointField],
        *,
        width: int | None = None,
        height: int = 1,
        row_step: int | None = None,
        is_bigendian: bool = False,
        is_dense: bool = True,
        frame_id: str = "velodyne",
    ) -> None:
        self.data = record.tobytes()
        self.fields = fields
        self.point_step = record.dtype.itemsize
        self.width = record.size // height if width is None else width
        self.height = height
        self.row_step = self.width * self.point_step if row_step is None else row_step
        self.is_bigendian = is_bigendian
        self.is_dense = is_dense
        self.header = FakeHeader(frame_id)


def _xyz_dtype(itemsize: int = 12, order: str = "<") -> np.dtype:
    return np.dtype({
        "names": ["x", "y", "z"],
        "formats": [f"{order}f4"] * 3,
        "offsets": [0, 4, 8],
        "itemsize": itemsize,
    })


XYZ_FIELDS = [
    PointField(name="x", offset=0, datatype=FLOAT32),
    PointField(name="y", offset=4, datatype=FLOAT32),
    PointField(name="z", offset=8, datatype=FLOAT32),
]


def test_dtype_honors_point_step_padding() -> None:
    dtype = fields_to_dtype(XYZ_FIELDS, point_step=32)
    assert dtype.itemsize == 32
    assert dtype.names == ("x", "y", "z")


def test_dtype_rejects_a_point_step_that_is_too_small() -> None:
    with pytest.raises(ValueError, match="point_step"):
        fields_to_dtype(XYZ_FIELDS, point_step=8)


def test_dtype_rejects_unknown_datatypes() -> None:
    with pytest.raises(ValueError, match="datatype"):
        fields_to_dtype([PointField(name="x", offset=0, datatype=99)], point_step=8)


def test_dtype_supports_array_fields() -> None:
    dtype = fields_to_dtype([PointField(name="rgb", offset=0, datatype=UINT8, count=4)], point_step=4)
    assert dtype["rgb"].shape == (4,)


def test_read_points_is_a_zero_copy_view() -> None:
    record = np.zeros(3, dtype=_xyz_dtype())
    record["x"] = [1.0, 2.0, 3.0]
    points = read_points(record.tobytes(), XYZ_FIELDS, width=3, point_step=12)
    np.testing.assert_allclose(points["x"], [1.0, 2.0, 3.0])
    # A view, not a copy: the array does not own its data.
    assert points.base is not None


def test_read_points_skips_padded_rows() -> None:
    # An organized 2x2 cloud whose rows carry 8 bytes of trailing padding.
    dtype = _xyz_dtype(itemsize=12)
    rows = []
    for row in range(2):
        record = np.zeros(2, dtype=dtype)
        record["x"] = [row * 10.0, row * 10.0 + 1.0]
        rows.append(record.tobytes() + b"\x00" * 8)

    points = read_points(b"".join(rows), XYZ_FIELDS, width=2, height=2, point_step=12, row_step=32)
    np.testing.assert_allclose(points["x"], [0.0, 1.0, 10.0, 11.0])


def test_read_points_can_stay_organized() -> None:
    record = np.zeros(6, dtype=_xyz_dtype())
    points = read_points(record.tobytes(), XYZ_FIELDS, width=3, height=2, point_step=12, organized=True)
    assert points.shape == (2, 3)


def test_read_points_rejects_a_short_buffer() -> None:
    with pytest.raises(ValueError, match="bytes"):
        read_points(b"\x00" * 8, XYZ_FIELDS, width=3, point_step=12)


def test_read_points_drops_non_finite_points_when_not_dense() -> None:
    record = np.zeros(3, dtype=_xyz_dtype())
    record["x"] = [1.0, np.nan, 3.0]
    points = read_points(record.tobytes(), XYZ_FIELDS, width=3, point_step=12, is_dense=False)
    np.testing.assert_allclose(points["x"], [1.0, 3.0])


def test_read_points_keeps_non_finite_points_when_dense() -> None:
    record = np.zeros(3, dtype=_xyz_dtype())
    record["x"] = [1.0, np.nan, 3.0]
    points = read_points(record.tobytes(), XYZ_FIELDS, width=3, point_step=12, is_dense=True)
    assert points.shape == (3,)


def test_big_endian_clouds_are_byteswapped() -> None:
    record = np.zeros(2, dtype=_xyz_dtype(order=">"))
    record["x"] = [1.5, -2.5]
    cloud = FakeCloud(record, XYZ_FIELDS, is_bigendian=True)
    decoded = decode_pointcloud2(cloud)
    np.testing.assert_allclose(decoded.positions[:, 0], [1.5, -2.5])


def test_unpack_rgb_from_uint32() -> None:
    np.testing.assert_array_equal(unpack_rgb(np.array([0x00FF8000], dtype=np.uint32)), [[255, 128, 0]])


def test_unpack_rgb_from_the_float32_hack() -> None:
    # Drivers routinely declare the packed color slot as FLOAT32; the bits are
    # still an 0x00RRGGBB integer and must be reinterpreted, not rounded.
    packed = np.array([0x00123456], dtype=np.uint32).view(np.float32)
    np.testing.assert_array_equal(unpack_rgb(packed), [[0x12, 0x34, 0x56]])


def test_velodyne_layout_with_ring_and_time() -> None:
    dtype = np.dtype({
        "names": ["x", "y", "z", "intensity", "ring", "time"],
        "formats": ["<f4", "<f4", "<f4", "<f4", "<u2", "<f4"],
        "offsets": [0, 4, 8, 16, 20, 24],
        "itemsize": 32,
    })
    record = np.zeros(4, dtype=dtype)
    record["x"] = [0.0, 1.0, 2.0, 3.0]
    record["intensity"] = [10.0, 20.0, 30.0, 40.0]
    record["ring"] = [0, 1, 2, 3]
    record["time"] = [0.0, 0.01, 0.02, 0.03]

    fields = [
        PointField(name="x", offset=0, datatype=FLOAT32),
        PointField(name="y", offset=4, datatype=FLOAT32),
        PointField(name="z", offset=8, datatype=FLOAT32),
        PointField(name="intensity", offset=16, datatype=FLOAT32),
        PointField(name="ring", offset=20, datatype=UINT16),
        PointField(name="time", offset=24, datatype=FLOAT32),
    ]
    decoded = decode_pointcloud2(FakeCloud(record, fields))

    assert len(decoded) == 4
    np.testing.assert_allclose(decoded.positions[:, 0], [0.0, 1.0, 2.0, 3.0])
    np.testing.assert_allclose(decoded.intensity, [10.0, 20.0, 30.0, 40.0])
    np.testing.assert_array_equal(decoded.ring, [0, 1, 2, 3])
    # Float `time` fields are already in seconds.
    np.testing.assert_allclose(decoded.times, [0.0, 0.01, 0.02, 0.03])
    assert decoded.frame_id == "velodyne"


def test_ouster_layout_converts_nanosecond_stamps() -> None:
    dtype = np.dtype({
        "names": ["x", "y", "z", "intensity", "t", "reflectivity", "ring"],
        "formats": ["<f4", "<f4", "<f4", "<f4", "<u4", "<u2", "<u2"],
        "offsets": [0, 4, 8, 16, 20, 24, 26],
        "itemsize": 48,
    })
    record = np.zeros(2, dtype=dtype)
    record["t"] = [0, 500_000]
    record["ring"] = [7, 8]

    fields = [
        PointField(name="x", offset=0, datatype=FLOAT32),
        PointField(name="y", offset=4, datatype=FLOAT32),
        PointField(name="z", offset=8, datatype=FLOAT32),
        PointField(name="intensity", offset=16, datatype=FLOAT32),
        PointField(name="t", offset=20, datatype=UINT32),
        PointField(name="reflectivity", offset=24, datatype=UINT16),
        PointField(name="ring", offset=26, datatype=UINT16),
    ]
    decoded = decode_pointcloud2(FakeCloud(record, fields, frame_id="os_sensor"))

    # Integer time fields are nanoseconds since the start of the sweep.
    np.testing.assert_allclose(decoded.times, [0.0, 5e-4])
    np.testing.assert_array_equal(decoded.ring, [7, 8])


def test_livox_layout_with_tag_and_line() -> None:
    dtype = np.dtype({
        "names": ["x", "y", "z", "intensity", "tag", "line", "timestamp"],
        "formats": ["<f4", "<f4", "<f4", "<u1", "<u1", "<u1", "<f8"],
        "offsets": [0, 4, 8, 12, 13, 14, 16],
        "itemsize": 24,
    })
    record = np.zeros(3, dtype=dtype)
    record["z"] = [1.0, 2.0, 3.0]
    record["line"] = [0, 1, 2]

    fields = [
        PointField(name="x", offset=0, datatype=FLOAT32),
        PointField(name="y", offset=4, datatype=FLOAT32),
        PointField(name="z", offset=8, datatype=FLOAT32),
        PointField(name="intensity", offset=12, datatype=UINT8),
        PointField(name="tag", offset=13, datatype=UINT8),
        PointField(name="line", offset=14, datatype=UINT8),
        PointField(name="timestamp", offset=16, datatype=8),
    ]
    decoded = decode_pointcloud2(FakeCloud(record, fields, frame_id="livox_frame"))

    np.testing.assert_allclose(decoded.positions[:, 2], [1.0, 2.0, 3.0])
    # `line` is Livox's spelling of `ring`.
    np.testing.assert_array_equal(decoded.ring, [0, 1, 2])


def test_rgbd_layout_unpacks_colors() -> None:
    dtype = np.dtype({
        "names": ["x", "y", "z", "rgb"],
        "formats": ["<f4", "<f4", "<f4", "<f4"],
        "offsets": [0, 4, 8, 16],
        "itemsize": 32,
    })
    record = np.zeros(2, dtype=dtype)
    record["rgb"] = np.array([0x00FF0000, 0x000000FF], dtype=np.uint32).view(np.float32)

    fields = [
        PointField(name="x", offset=0, datatype=FLOAT32),
        PointField(name="y", offset=4, datatype=FLOAT32),
        PointField(name="z", offset=8, datatype=FLOAT32),
        PointField(name="rgb", offset=16, datatype=FLOAT32),
    ]
    decoded = decode_pointcloud2(FakeCloud(record, fields, frame_id="camera_depth_optical_frame"))

    np.testing.assert_array_equal(decoded.colors, [[255, 0, 0], [0, 0, 255]])
    assert decoded.intensity is None


def test_decode_requires_xyz() -> None:
    dtype = np.dtype([("intensity", "<f4")])
    fields = [PointField(name="intensity", offset=0, datatype=FLOAT32)]
    with pytest.raises(ValueError, match="missing"):
        decode_pointcloud2(FakeCloud(np.zeros(2, dtype=dtype), fields))
