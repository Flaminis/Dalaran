"""Minimal duck-typed stand-ins for the ROS 2 messages the converters consume."""

from __future__ import annotations

from typing import Any, Sequence


class Simple:
    """A namespace whose attributes come from keyword arguments."""

    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__dict__})"


def vec3(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Simple:
    """A `geometry_msgs/Vector3` or `geometry_msgs/Point`."""
    return Simple(x=x, y=y, z=z)


def quat(x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 1.0) -> Simple:
    """A `geometry_msgs/Quaternion`, in ROS's `xyzw` order."""
    return Simple(x=x, y=y, z=z, w=w)


def pose(position: Simple | None = None, orientation: Simple | None = None) -> Simple:
    """A `geometry_msgs/Pose`."""
    return Simple(position=position or vec3(), orientation=orientation or quat())


def header(frame_id: str = "", sec: int = 0, nanosec: int = 0) -> Simple:
    """A `std_msgs/Header`."""
    return Simple(frame_id=frame_id, stamp=Simple(sec=sec, nanosec=nanosec))


def color(r: float = 0.0, g: float = 0.0, b: float = 0.0, a: float = 1.0) -> Simple:
    """A `std_msgs/ColorRGBA`, with components in `[0, 1]`."""
    return Simple(r=r, g=g, b=b, a=a)


def transform_stamped(
    parent: str,
    child: str,
    translation: Sequence[float] = (0.0, 0.0, 0.0),
    rotation: Sequence[float] = (0.0, 0.0, 0.0, 1.0),
) -> Simple:
    """A `geometry_msgs/TransformStamped`."""
    return Simple(
        header=header(frame_id=parent),
        child_frame_id=child,
        transform=Simple(translation=vec3(*translation), rotation=quat(*rotation)),
    )
