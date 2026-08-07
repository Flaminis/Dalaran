"""
Pure helpers that decide *where* and *how often* a ROS 2 topic gets logged.

Topic naming, allow/deny filtering, per-topic rate limiting and header-stamp
handling are all pure functions over plain data, deliberately separated from the
`rclpy` machinery in [`dalaran.ros2.bridge`][]. That makes the routing rules -
the part users actually tune - testable without a ROS installation, and reusable
for offline rosbag replay.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

__all__ = [
    "Throttler",
    "TopicFilter",
    "entity_path_join",
    "sanitize_path_part",
    "stamp_to_nanos",
    "topic_to_entity_path",
]

# Entity path parts are slash separated, so anything that is not a plain path
# character gets folded into an underscore.
_INVALID_PART = re.compile(r"[^A-Za-z0-9_.\-]+")


def sanitize_path_part(part: str) -> str:
    """
    Make a single ROS name component safe to use as an entity path part.

    Examples
    --------
    ```python
    from dalaran.ros2.naming import sanitize_path_part

    assert sanitize_path_part("image raw!") == "image_raw_"
    ```

    """
    return _INVALID_PART.sub("_", part)


def entity_path_join(*parts: str) -> str:
    """
    Join entity path parts, dropping empty ones and collapsing separators.

    Examples
    --------
    ```python
    from dalaran.ros2.naming import entity_path_join

    assert entity_path_join("robots/spot", "", "lidar") == "robots/spot/lidar"
    ```

    """
    pieces: list[str] = []
    for part in parts:
        for piece in str(part).split("/"):
            if piece:
                pieces.append(piece)
    return "/".join(pieces)


def topic_to_entity_path(
    topic: str,
    *,
    prefix: str = "",
    overrides: dict[str, str] | None = None,
) -> str:
    """
    Map a ROS 2 topic name onto a Dalaran entity path.

    The mapping is intentionally boring: `/camera/color/image_raw` becomes
    `camera/color/image_raw`, so the entity tree in the viewer mirrors the topic
    tree you already know from `ros2 topic list`. A `prefix` puts a whole robot
    under its own subtree, and `overrides` lets you re-home individual topics -
    which is how you graft a sensor topic onto its frame in the transform tree.

    Parameters
    ----------
    topic:
        The ROS topic name, with or without a leading slash.
    prefix:
        Entity path to nest everything under, e.g. `"robots/spot"`.
    overrides:
        Exact topic name to entity path mapping, applied before the default
        rule. The override result is still nested under `prefix`.

    Returns
    -------
    str
        The entity path to log this topic's messages to.

    Examples
    --------
    ```python
    from dalaran.ros2.naming import topic_to_entity_path

    assert topic_to_entity_path("/scan") == "scan"
    assert topic_to_entity_path("/scan", prefix="robots/spot") == "robots/spot/scan"
    assert (
        topic_to_entity_path("/scan", overrides={"/scan": "world/base_link/lidar"})
        == "world/base_link/lidar"
    )
    ```

    """
    normalized = "/" + topic.strip("/") if topic.strip("/") else "/"
    if overrides:
        override = overrides.get(normalized) or overrides.get(topic)
        if override is not None:
            return entity_path_join(prefix, override)

    parts = [sanitize_path_part(part) for part in normalized.split("/") if part]
    return entity_path_join(prefix, *parts)


@dataclass
class TopicFilter:
    """
    Glob-based allow/deny filtering for topics.

    Deny always wins over allow, and an empty allow list means "everything is
    allowed". Patterns are ordinary shell globs matched against the normalized
    (leading-slash) topic name, so `/camera/*` and `*/image_raw` both work.

    Parameters
    ----------
    allow:
        Patterns a topic must match at least one of. Empty means allow all.
    deny:
        Patterns that exclude a topic outright.

    Examples
    --------
    ```python
    from dalaran.ros2.naming import TopicFilter

    only_sensors = TopicFilter(allow=["/scan", "/camera/*"], deny=["*/compressed*"])
    assert only_sensors.accepts("/camera/color/image_raw")
    assert not only_sensors.accepts("/camera/color/image_raw/compressed")
    assert not only_sensors.accepts("/rosout")
    ```

    """

    allow: Sequence[str] = field(default_factory=tuple)
    deny: Sequence[str] = field(default_factory=tuple)

    def accepts(self, topic: str) -> bool:
        """Return whether `topic` should be logged."""
        normalized = "/" + topic.strip("/")
        if any(fnmatchcase(normalized, pattern) for pattern in self.deny):
            return False
        if not self.allow:
            return True
        return any(fnmatchcase(normalized, pattern) for pattern in self.allow)

    def filter(self, topics: Iterable[str]) -> list[str]:
        """Return the accepted subset of `topics`, preserving order."""
        return [topic for topic in topics if self.accepts(topic)]


@dataclass
class Throttler:
    """
    Per-topic rate limiting, so a 3000 Hz IMU cannot drown a 10 Hz map.

    Rates are given in Hz and may be set per topic glob, with a `default` for
    everything else. `None` means "no limit". The throttler is deliberately
    stateful but pure: you feed it a timestamp, it answers yes or no, and it
    never looks at a clock itself - which makes it behave identically for live
    subscriptions and for accelerated bag replay.

    Parameters
    ----------
    default:
        Maximum rate in Hz for topics with no specific rule.
    rules:
        Topic glob to maximum rate in Hz. The first matching rule wins.

    Examples
    --------
    ```python
    from dalaran.ros2.naming import Throttler

    throttle = Throttler(rules={"/imu": 2.0})
    assert throttle.should_log("/imu", 0.0)
    assert not throttle.should_log("/imu", 0.1)  # too soon, 2 Hz means 0.5 s
    assert throttle.should_log("/imu", 0.6)
    ```

    """

    default: float | None = None
    rules: dict[str, float] = field(default_factory=dict)
    _last: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def rate_for(self, topic: str) -> float | None:
        """Return the maximum rate in Hz that applies to `topic`."""
        normalized = "/" + topic.strip("/")
        for pattern, rate in self.rules.items():
            if fnmatchcase(normalized, pattern) or fnmatchcase(normalized, "/" + pattern.strip("/")):
                return rate
        return self.default

    def should_log(self, topic: str, timestamp: float) -> bool:
        """
        Return whether a message on `topic` at `timestamp` (in seconds) passes the limit.

        Accepting a message updates the internal state, so call this exactly once
        per message.
        """
        rate = self.rate_for(topic)
        if rate is None or rate <= 0.0:
            return True

        interval = 1.0 / rate
        previous = self._last.get(topic)
        if previous is not None and timestamp - previous < interval:
            # Time going backwards means a new bag loop or a `/clock` jump; let it through.
            if timestamp >= previous:
                return False
        self._last[topic] = timestamp
        return True

    def reset(self) -> None:
        """Forget all per-topic state, e.g. when a bag loops."""
        self._last.clear()


def stamp_to_nanos(stamp: Any) -> int | None:
    """
    Convert a `builtin_interfaces/Time` (or a `std_msgs/Header`) to integer nanoseconds.

    Returns `None` for the all-zero stamp ROS uses to mean "no time given", so
    callers can fall back to the wall clock instead of logging everything at the
    epoch.

    Examples
    --------
    ```python
    from dalaran.ros2.naming import stamp_to_nanos


    class Stamp:
        sec, nanosec = 3, 500_000_000


    assert stamp_to_nanos(Stamp()) == 3_500_000_000
    ```

    """
    if stamp is None:
        return None
    if hasattr(stamp, "stamp"):
        stamp = stamp.stamp
    sec = getattr(stamp, "sec", None)
    nanosec = getattr(stamp, "nanosec", getattr(stamp, "nsec", None))
    if sec is None and nanosec is None:
        return None
    total = int(sec or 0) * 1_000_000_000 + int(nanosec or 0)
    return total if total != 0 else None
