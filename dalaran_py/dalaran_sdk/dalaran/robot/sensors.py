"""
Conventional, correct logging helpers for the sensors robots actually ship with.

Every helper here encodes the convention that goes with the sensor, so that a
laser scan ends up in the robot's REP-103 FLU body frame and a camera ends up in
an RDF optical frame, instead of whatever the caller happened to guess.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import numpy.typing as npt

from ._math import quaternion_to_matrix

if TYPE_CHECKING:
    from dalaran.recording_stream import RecordingStream

__all__ = [
    "colormap_scalars",
    "laser_scan_to_points",
    "log_camera",
    "log_imu",
    "log_lidar_scan",
    "log_pointcloud",
]


def laser_scan_to_points(
    ranges: npt.ArrayLike,
    *,
    angle_min: float,
    angle_increment: float | None = None,
    angle_max: float | None = None,
    range_min: float = 0.0,
    range_max: float = float("inf"),
    z: float = 0.0,
) -> npt.NDArray[np.float32]:
    """
    Project a ROS-style 2D laser scan into `(N, 3)` cartesian points.

    Beams whose range is non-finite (the `inf` a lidar reports for "no return",
    or a `nan` dropout) or outside `[range_min, range_max]` are dropped, which is
    exactly what `sensor_msgs/LaserScan` consumers are expected to do. The output
    is in the sensor's own REP-103 FLU frame: angle zero points along +X
    (forward) and angles increase towards +Y (left).

    Parameters
    ----------
    ranges:
        `(N,)` beam distances in meters.
    angle_min:
        Angle of the first beam, in radians.
    angle_increment:
        Angular step between beams, in radians. Mutually exclusive with `angle_max`.
    angle_max:
        Angle of the last beam, in radians. Mutually exclusive with `angle_increment`.
    range_min:
        Beams closer than this are discarded.
    range_max:
        Beams further than this are discarded.
    z:
        Height of the scan plane in the sensor frame.

    Returns
    -------
    numpy.ndarray
        `(M, 3)` float32 points, with `M <= N` after invalid beams are dropped.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot import laser_scan_to_points

    # Four beams at 0, 90, 180, 270 degrees; the third one had no return.
    points = laser_scan_to_points(
        [1.0, 2.0, np.inf, 4.0],
        angle_min=0.0,
        angle_increment=np.pi / 2,
    )
    np.testing.assert_allclose(points[0], [1.0, 0.0, 0.0], atol=1e-6)
    np.testing.assert_allclose(points[1], [0.0, 2.0, 0.0], atol=1e-6)
    assert len(points) == 3
    ```

    """
    r = np.asarray(ranges, dtype=np.float64).reshape(-1)
    count = r.shape[0]

    if (angle_increment is None) == (angle_max is None):
        msg = "Pass exactly one of `angle_increment` or `angle_max`"
        raise ValueError(msg)

    if angle_increment is None:
        assert angle_max is not None
        angle_increment = (angle_max - angle_min) / (count - 1) if count > 1 else 0.0

    angles = angle_min + angle_increment * np.arange(count, dtype=np.float64)

    valid = np.isfinite(r) & (r >= range_min) & (r <= range_max)
    r = r[valid]
    angles = angles[valid]

    out = np.empty((r.shape[0], 3), dtype=np.float32)
    out[:, 0] = r * np.cos(angles)
    out[:, 1] = r * np.sin(angles)
    out[:, 2] = z
    return out


def colormap_scalars(
    values: npt.ArrayLike,
    *,
    vmin: float | None = None,
    vmax: float | None = None,
) -> npt.NDArray[np.uint8]:
    """
    Map scalars (intensity, height, reflectivity, ...) to `(N, 3)` uint8 turbo colors.

    The range is normalized to `[vmin, vmax]`, defaulting to the data's own
    finite min/max. Non-finite values are clamped rather than dropped, so the
    output always has the same length as the input.

    Examples
    --------
    ```python
    import numpy as np
    from dalaran.robot import colormap_scalars

    colors = colormap_scalars([0.0, 0.5, 1.0])
    assert colors.shape == (3, 3) and colors.dtype == np.uint8
    ```

    """
    from dalaran.utilities._turbo import turbo_colormap_data

    v = np.asarray(values, dtype=np.float64).reshape(-1)
    finite = v[np.isfinite(v)]
    lo = float(vmin) if vmin is not None else (float(finite.min()) if finite.size else 0.0)
    hi = float(vmax) if vmax is not None else (float(finite.max()) if finite.size else 1.0)
    if hi <= lo:
        hi = lo + 1.0

    t = np.clip((np.nan_to_num(v, nan=lo, posinf=hi, neginf=lo) - lo) / (hi - lo), 0.0, 1.0)
    idx = np.round(t * (len(turbo_colormap_data) - 1)).astype(np.int64)
    return (turbo_colormap_data[idx] * 255.0 + 0.5).astype(np.uint8)


def log_lidar_scan(
    entity_path: str,
    ranges: npt.ArrayLike,
    *,
    angle_min: float,
    angle_increment: float | None = None,
    angle_max: float | None = None,
    range_min: float = 0.0,
    range_max: float = float("inf"),
    z: float = 0.0,
    radii: float = 0.02,
    colors: npt.ArrayLike | None = None,
    colorize_by_range: bool = False,
    recording: RecordingStream | None = None,
) -> npt.NDArray[np.float32]:
    """
    Log a `sensor_msgs/LaserScan`-style 2D scan as a point cloud.

    The points are logged in the sensor's own frame, so `entity_path` should be
    the entity of the lidar frame itself (for example
    `tree.entity_path("lidar")`); the transform tree then places the scan in the
    world for you.

    Parameters
    ----------
    entity_path:
        Path to the lidar entity, e.g. `"world/base_link/lidar"`.
    ranges:
        `(N,)` beam distances in meters. `inf`/`nan` beams are dropped.
    angle_min:
        Angle of the first beam, in radians.
    angle_increment:
        Angular step between beams. Mutually exclusive with `angle_max`.
    angle_max:
        Angle of the last beam. Mutually exclusive with `angle_increment`.
    range_min:
        Beams closer than this are discarded.
    range_max:
        Beams further than this are discarded.
    z:
        Height of the scan plane in the sensor frame.
    radii:
        Point radius in meters.
    colors:
        Optional explicit colors, one per *valid* beam.
    colorize_by_range:
        Colorize the surviving points by distance using the turbo colormap.
    recording:
        Specifies the [`dalaran.RecordingStream`][] to use. If left unspecified,
        defaults to the current active data recording, if there is one.

    Returns
    -------
    numpy.ndarray
        The `(M, 3)` points that were logged.

    Examples
    --------
    ```python
    import numpy as np
    import dalaran as dl

    dl.init("dalaran_example_lidar", spawn=True)

    ranges = 3.0 + np.sin(np.linspace(0.0, 8.0 * np.pi, 360))
    dl.robot.log_lidar_scan(
        "world/base_link/lidar",
        ranges,
        angle_min=-np.pi,
        angle_increment=2.0 * np.pi / 360.0,
        colorize_by_range=True,
    )
    ```

    """
    import dalaran as dl

    points = laser_scan_to_points(
        ranges,
        angle_min=angle_min,
        angle_increment=angle_increment,
        angle_max=angle_max,
        range_min=range_min,
        range_max=range_max,
        z=z,
    )

    if colors is None and colorize_by_range:
        colors = colormap_scalars(np.linalg.norm(points[:, :2], axis=1))

    dl.log(
        entity_path,
        dl.Points3D(points, radii=radii, colors=colors),
        recording=recording,
    )
    return points


def log_pointcloud(
    entity_path: str,
    positions: npt.ArrayLike,
    *,
    intensity: npt.ArrayLike | None = None,
    colors: npt.ArrayLike | None = None,
    radii: float | npt.ArrayLike = 0.01,
    vmin: float | None = None,
    vmax: float | None = None,
    recording: RecordingStream | None = None,
) -> None:
    """
    Log an `(N, 3)` point cloud, optionally colormapped by a per-point scalar.

    Parameters
    ----------
    entity_path:
        Path to the sensor entity the cloud is expressed in.
    positions:
        `(N, 3)` xyz positions in the sensor frame.
    intensity:
        Optional `(N,)` scalar per point (intensity, reflectivity, height, ...),
        mapped through the turbo colormap. Ignored if `colors` is given.
    colors:
        Optional explicit `(N, 3)` or `(N, 4)` colors.
    radii:
        Point radius (or radii) in meters.
    vmin:
        Lower end of the intensity range. Defaults to the data minimum.
    vmax:
        Upper end of the intensity range. Defaults to the data maximum.
    recording:
        Specifies the [`dalaran.RecordingStream`][] to use. If left unspecified,
        defaults to the current active data recording, if there is one.

    Examples
    --------
    ```python
    import numpy as np
    import dalaran as dl

    dl.init("dalaran_example_pointcloud", spawn=True)

    xyz = np.random.default_rng(0).normal(size=(1000, 3))
    dl.robot.log_pointcloud("world/base_link/lidar", xyz, intensity=xyz[:, 2])
    ```

    """
    import dalaran as dl

    xyz = np.asarray(positions, dtype=np.float32)
    if xyz.ndim != 2 or xyz.shape[1] != 3:
        msg = f"`positions` must have shape (N, 3), got {xyz.shape}"
        raise ValueError(msg)

    if colors is None and intensity is not None:
        values = np.asarray(intensity, dtype=np.float64).reshape(-1)
        if values.shape[0] != xyz.shape[0]:
            msg = f"`intensity` must have one value per point, got {values.shape[0]} for {xyz.shape[0]} points"
            raise ValueError(msg)
        colors = colormap_scalars(values, vmin=vmin, vmax=vmax)

    dl.log(entity_path, dl.Points3D(xyz, colors=colors, radii=radii), recording=recording)


def log_imu(
    entity_path: str,
    *,
    linear_acceleration: npt.ArrayLike | None = None,
    angular_velocity: npt.ArrayLike | None = None,
    orientation: npt.ArrayLike | None = None,
    acceleration_scale: float = 0.1,
    angular_velocity_scale: float = 1.0,
    recording: RecordingStream | None = None,
) -> None:
    """
    Log a `sensor_msgs/Imu`-style reading.

    The linear acceleration and angular velocity are logged both as scalar time
    series (one entity per axis, so they show up in a timeseries view) and as 3D
    arrows in the IMU frame, which is by far the fastest way to spot a swapped
    axis or a sign error.

    Parameters
    ----------
    entity_path:
        Path to the IMU entity, in a REP-103 FLU frame.
    linear_acceleration:
        `(3,)` linear acceleration in m/s^2, including gravity.
    angular_velocity:
        `(3,)` body rates in rad/s.
    orientation:
        Optional `(4,)` orientation quaternion in `xyzw` order. When given, it is
        logged as the IMU entity's transform.
    acceleration_scale:
        Arrow length per m/s^2. The default keeps a 9.81 m/s^2 gravity vector
        roughly one meter long.
    angular_velocity_scale:
        Arrow length per rad/s.
    recording:
        Specifies the [`dalaran.RecordingStream`][] to use. If left unspecified,
        defaults to the current active data recording, if there is one.

    Examples
    --------
    ```python
    import dalaran as dl

    dl.init("dalaran_example_imu", spawn=True)

    dl.robot.log_imu(
        "world/base_link/imu",
        linear_acceleration=[0.0, 0.0, 9.81],
        angular_velocity=[0.0, 0.0, 0.2],
    )
    ```

    """
    import dalaran as dl

    if orientation is not None:
        quat = np.asarray(orientation, dtype=np.float64).reshape(4)
        # Validate early: a zero quaternion would silently corrupt the scene.
        quaternion_to_matrix(quat)
        dl.log(entity_path, dl.Transform3D(quaternion=quat), recording=recording)

    for name, value, scale, color in (
        ("linear_acceleration", linear_acceleration, acceleration_scale, (255, 90, 60)),
        ("angular_velocity", angular_velocity, angular_velocity_scale, (60, 170, 255)),
    ):
        if value is None:
            continue
        vec = np.asarray(value, dtype=np.float64).reshape(3)
        dl.log(
            f"{entity_path}/{name}",
            dl.Arrows3D(vectors=[vec * scale], origins=[[0.0, 0.0, 0.0]], colors=[color]),
            recording=recording,
        )
        for axis, component in zip("xyz", vec):
            dl.log(f"{entity_path}/{name}/{axis}", dl.Scalars(float(component)), recording=recording)


def log_camera(
    entity_path: str,
    *,
    width: int,
    height: int,
    fx: float | None = None,
    fy: float | None = None,
    cx: float | None = None,
    cy: float | None = None,
    intrinsics: npt.ArrayLike | None = None,
    image: npt.ArrayLike | None = None,
    depth_image: npt.ArrayLike | None = None,
    depth_meter: float | None = None,
    image_plane_distance: float | None = None,
    recording: RecordingStream | None = None,
) -> None:
    """
    Log a pinhole camera and, optionally, the image it produced.

    Intrinsics may be given either as `fx`/`fy`/`cx`/`cy` or as a full 3x3 `K`
    matrix; `fy` defaults to `fx` and the principal point defaults to the image
    center. The camera entity is an RDF optical frame (`x` right, `y` down,
    `z` forward), which is the convention every `K` matrix is written in, so
    parent it to your FLU body frame with the usual optical rotation.

    Parameters
    ----------
    entity_path:
        Path to the camera's optical-frame entity.
    width:
        Image width in pixels.
    height:
        Image height in pixels.
    fx:
        Horizontal focal length in pixels.
    fy:
        Vertical focal length in pixels. Defaults to `fx`.
    cx:
        Horizontal principal point in pixels. Defaults to `width / 2`.
    cy:
        Vertical principal point in pixels. Defaults to `height / 2`.
    intrinsics:
        A full `(3, 3)` row-major `K` matrix. Mutually exclusive with `fx`.
    image:
        Optional `(H, W)`, `(H, W, 3)` or `(H, W, 4)` color image, logged as
        `<entity_path>/image`.
    depth_image:
        Optional `(H, W)` depth image, logged as `<entity_path>/depth`.
    depth_meter:
        How many depth-image units correspond to one meter.
    image_plane_distance:
        How far away the image plane is drawn in the 3D view, in meters.
    recording:
        Specifies the [`dalaran.RecordingStream`][] to use. If left unspecified,
        defaults to the current active data recording, if there is one.

    Examples
    --------
    ```python
    import numpy as np
    import dalaran as dl

    dl.init("dalaran_example_camera", spawn=True)

    dl.robot.log_camera(
        "world/base_link/camera",
        width=640,
        height=480,
        fx=525.0,
        image=np.zeros((480, 640, 3), dtype=np.uint8),
    )
    ```

    """
    import dalaran as dl

    if (intrinsics is None) == (fx is None):
        msg = "Pass exactly one of `fx` or `intrinsics`"
        raise ValueError(msg)

    if intrinsics is not None:
        k = np.asarray(intrinsics, dtype=np.float32)
        if k.shape != (3, 3):
            msg = f"`intrinsics` must be a (3, 3) matrix, got shape {k.shape}"
            raise ValueError(msg)
    else:
        assert fx is not None
        f_y = fx if fy is None else fy
        p_x = width / 2.0 if cx is None else cx
        p_y = height / 2.0 if cy is None else cy
        k = np.array(
            [[fx, 0.0, p_x], [0.0, f_y, p_y], [0.0, 0.0, 1.0]],
            dtype=np.float32,
        )

    pinhole_kwargs: dict[str, Any] = {
        "image_from_camera": k,
        "resolution": [width, height],
        "camera_xyz": dl.ViewCoordinates.RDF,
    }
    if image_plane_distance is not None:
        pinhole_kwargs["image_plane_distance"] = image_plane_distance

    dl.log(entity_path, dl.Pinhole(**pinhole_kwargs), recording=recording)

    if image is not None:
        dl.log(f"{entity_path}/image", dl.Image(image), recording=recording)
    if depth_image is not None:
        dl.log(
            f"{entity_path}/depth",
            dl.DepthImage(depth_image, meter=depth_meter),
            recording=recording,
        )
