"""
`Ros2Bridge`: stream a live ROS 2 graph into a Dalaran recording.

The bridge is a normal ROS 2 node. It discovers topics, subscribes to the ones
you allowed with a QoS profile that actually matches the publisher, rate-limits
the firehose topics, and routes every message through the extensible converter
registry in [`dalaran.ros2.msg_map`][].

`rclpy` is imported lazily, inside the methods that need it, so `import
dalaran.ros2` keeps working on a laptop with no ROS installed - which matters
because the same package is used to replay rosbag2 files offline.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from .context import Context
from .msg_map import convert, lookup, lookup_topic, normalize_type_name
from .naming import Throttler, TopicFilter, stamp_to_nanos, topic_to_entity_path

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence

    from dalaran.recording_stream import RecordingStream

__all__ = ["DEFAULT_DENY", "QOS_PRESETS", "Ros2Bridge", "qos_profile"]

#: Topics that are never interesting to visualize and would only add noise.
DEFAULT_DENY: tuple[str, ...] = (
    "/rosout",
    "/parameter_events",
    "*/theora*",
    "*/compressedDepth",
)

#: The QoS presets a publisher in the wild is likely to be using.
#:
#: * `"sensor_data"` - best effort, small depth. What every driver publishes
#:   scans, images and clouds with. Subscribing reliably to a best-effort
#:   publisher silently receives nothing, which is the single most common
#:   "why is my topic empty" problem.
#: * `"reliable"` - reliable, volatile. The rclpy default.
#: * `"transient_local"` - reliable + transient local, i.e. latched. Required for
#:   `/map`, `/robot_description` and `/tf_static`, which publish once at startup.
#: * `"system_default"` - whatever the middleware defaults to.
QOS_PRESETS: tuple[str, ...] = ("sensor_data", "reliable", "transient_local", "system_default")

#: Topics whose publishers latch, so they need a transient-local subscription.
_LATCHED_TOPICS: tuple[str, ...] = ("/tf_static", "/map", "/map_metadata", "/robot_description")


def qos_profile(preset: str, *, depth: int = 10) -> Any:
    """
    Build an `rclpy` QoS profile from one of the [`QOS_PRESETS`][dalaran.ros2.QOS_PRESETS].

    Parameters
    ----------
    preset:
        One of `"sensor_data"`, `"reliable"`, `"transient_local"` or
        `"system_default"`.
    depth:
        History depth. Ignored by `"sensor_data"`, which uses its own depth of 5.

    Returns
    -------
    rclpy.qos.QoSProfile
        A profile ready to hand to `Node.create_subscription`.

    Examples
    --------
    ```python
    from dalaran.ros2 import QOS_PRESETS

    assert "transient_local" in QOS_PRESETS  # what /map and /tf_static need
    ```

    """
    from rclpy.qos import (
        DurabilityPolicy,
        HistoryPolicy,
        QoSProfile,
        ReliabilityPolicy,
        qos_profile_sensor_data,
        qos_profile_system_default,
    )

    if preset == "sensor_data":
        return qos_profile_sensor_data
    if preset == "system_default":
        return qos_profile_system_default
    if preset == "reliable":
        return QoSProfile(
            depth=depth,
            history=HistoryPolicy.KEEP_LAST,
            reliability=ReliabilityPolicy.RELIABLE,
        )
    if preset == "transient_local":
        return QoSProfile(
            depth=depth,
            history=HistoryPolicy.KEEP_LAST,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

    msg = f"Unknown QoS preset {preset!r}; expected one of {QOS_PRESETS}"
    raise ValueError(msg)


class Ros2Bridge:
    """
    Subscribe to a live ROS 2 graph and stream it into a Dalaran recording.

    Parameters
    ----------
    allow:
        Topic globs to subscribe to. Empty means "everything that has a
        converter".
    deny:
        Topic globs to skip. Defaults to
        [`DEFAULT_DENY`][dalaran.ros2.bridge.DEFAULT_DENY].
    max_hz:
        Per-topic-glob rate limits in Hz, e.g. `{"/camera/*": 5.0}`.
    default_max_hz:
        Rate limit applied to topics with no specific rule. `None` means
        unlimited.
    prefix:
        Entity path prefix, so several robots can share one recording.
    topic_paths:
        Explicit topic to entity path overrides, for grafting a topic onto a
        specific place in the entity tree.
    qos:
        Default QoS preset. Sensor drivers publish best effort, so
        `"sensor_data"` is the default here too.
    qos_overrides:
        Per-topic-glob QoS presets. Latched topics such as `/map` and
        `/tf_static` are given `"transient_local"` automatically.
    depth:
        History depth for the reliable and transient-local presets.
    node_name:
        The ROS node name to create.
    timeline:
        Name of the timeline driven by message header stamps.
    wall_timeline:
        Name of the timeline driven by the bridge's own wall clock. Messages
        without a usable header stamp only appear on this one.
    recording:
        The [`dalaran.RecordingStream`][] to log to.
    discovery_period:
        How often, in seconds, to look for newly advertised topics.
    on_unknown_type:
        Called once per unhandled message type, with the type name. Defaults to
        a one-line warning.

    Examples
    --------
    ```python
    import dalaran as dl
    from dalaran.ros2 import Ros2Bridge

    dl.init("dalaran_example_ros2_bridge", spawn=True)

    with Ros2Bridge(
        allow=["/tf", "/tf_static", "/scan", "/odom", "/map"],
        max_hz={"/scan": 10.0},
    ) as bridge:
        bridge.spin(duration=10.0)
    ```

    """

    def __init__(
        self,
        *,
        allow: Sequence[str] = (),
        deny: Sequence[str] = DEFAULT_DENY,
        max_hz: Mapping[str, float] | None = None,
        default_max_hz: float | None = None,
        prefix: str = "",
        topic_paths: Mapping[str, str] | None = None,
        qos: str = "sensor_data",
        qos_overrides: Mapping[str, str] | None = None,
        depth: int = 10,
        node_name: str = "dalaran_bridge",
        timeline: str = "ros_time",
        wall_timeline: str = "log_time",
        recording: RecordingStream | None = None,
        discovery_period: float = 2.0,
        on_unknown_type: Callable[[str], None] | None = None,
    ) -> None:
        self.filter = TopicFilter(allow=tuple(allow), deny=tuple(deny))
        self.throttler = Throttler(default=default_max_hz, rules=dict(max_hz or {}))
        self.topic_paths = dict(topic_paths or {})
        self.prefix = prefix
        self.qos = qos
        self.qos_overrides = dict(qos_overrides or {})
        self.depth = depth
        self.node_name = node_name
        self.timeline = timeline
        self.wall_timeline = wall_timeline
        self.discovery_period = discovery_period
        self.context = Context(recording=recording, prefix=prefix)

        self._node: Any = None
        self._subscriptions: dict[str, Any] = {}
        self._warned_types: set[str] = set()
        self._on_unknown_type = on_unknown_type or self._warn_unknown_type

    # -- routing (pure, and unit tested without ROS) -----------------------

    def entity_path_for(self, topic: str) -> str:
        """
        Return the entity path a topic's messages are logged to.

        Examples
        --------
        ```python
        from dalaran.ros2 import Ros2Bridge

        bridge = Ros2Bridge(prefix="robots/spot")
        assert bridge.entity_path_for("/camera/image_raw") == "robots/spot/camera/image_raw"
        ```

        """
        return topic_to_entity_path(topic, prefix=self.prefix, overrides=self.topic_paths)

    def qos_for(self, topic: str) -> str:
        """
        Return the QoS preset that will be used for `topic`.

        Latched topics are recognized by name, because subscribing to `/map` or
        `/tf_static` with a volatile profile is the classic way to end up with an
        empty map and a broken transform tree.

        Examples
        --------
        ```python
        from dalaran.ros2 import Ros2Bridge

        bridge = Ros2Bridge()
        assert bridge.qos_for("/scan") == "sensor_data"
        assert bridge.qos_for("/map") == "transient_local"
        assert bridge.qos_for("/tf_static") == "transient_local"
        ```

        """
        from fnmatch import fnmatchcase

        normalized = "/" + topic.strip("/")
        for pattern, preset in self.qos_overrides.items():
            if fnmatchcase(normalized, pattern):
                return preset
        if normalized in _LATCHED_TOPICS:
            return "transient_local"
        return self.qos

    def accepts(self, topic: str, type_name: str) -> bool:
        """
        Return whether a topic should be subscribed to at all.

        A topic must survive the allow/deny globs *and* have a registered
        converter; there is no point subscribing to a message type we cannot draw.
        """
        if not self.filter.accepts(topic):
            return False
        if lookup_topic(topic) is None and lookup(type_name) is None:
            if type_name not in self._warned_types:
                self._warned_types.add(type_name)
                self._on_unknown_type(type_name)
            return False
        return True

    def handle_message(self, topic: str, type_name: str, msg: Any, *, wall_time: float | None = None) -> bool:
        """
        Route one message: throttle, set the timelines, convert and log.

        This is the whole per-message path, and it is deliberately free of
        `rclpy`, so it can be driven from a live subscription, from a rosbag2
        replay, or from a test with hand-built messages.

        Parameters
        ----------
        topic:
            The topic the message arrived on.
        type_name:
            The message's ROS type name, in any accepted spelling.
        msg:
            The message itself.
        wall_time:
            Wall-clock seconds to stamp the wall timeline with. Defaults to now.

        Returns
        -------
        bool
            Whether the message was converted, i.e. `False` if it was throttled
            away or had no converter.

        """
        stamp_ns = stamp_to_nanos(getattr(msg, "header", None))
        wall_time = time.time() if wall_time is None else wall_time
        throttle_time = stamp_ns * 1e-9 if stamp_ns is not None else wall_time
        if not self.throttler.should_log(topic, throttle_time):
            return False

        import numpy as np

        if stamp_ns is not None:
            self.context.set_time(self.timeline, timestamp=np.datetime64(stamp_ns, "ns"))
        self.context.set_time(self.wall_timeline, timestamp=np.datetime64(int(wall_time * 1e9), "ns"))

        return convert(type_name, msg, self.entity_path_for(topic), self.context, topic=topic)

    # -- ROS plumbing (rclpy is imported lazily, here and nowhere else) -----

    @staticmethod
    def _warn_unknown_type(type_name: str) -> None:
        import logging

        logging.getLogger("dalaran.ros2").info(
            "No Dalaran converter registered for %r; register one with `@dalaran.ros2.register(%r)` to visualize it",
            type_name,
            type_name,
        )

    @property
    def node(self) -> Any:
        """The underlying `rclpy` node, created on first access."""
        if self._node is None:
            self.start()
        return self._node

    def start(self) -> Any:
        """Initialize `rclpy` if needed and create the bridge node."""
        import rclpy

        if not rclpy.ok():
            rclpy.init()
        if self._node is None:
            self._node = rclpy.create_node(self.node_name)
        return self._node

    def discover(self) -> list[tuple[str, str]]:
        """
        Return the `(topic, type_name)` pairs currently worth subscribing to.

        Topics advertising several types are skipped, because a single entity
        path cannot sensibly hold two different message types.
        """
        found: list[tuple[str, str]] = []
        for topic, type_names in self.node.get_topic_names_and_types():
            if len(type_names) != 1:
                continue
            type_name = normalize_type_name(type_names[0])
            if self.accepts(topic, type_name):
                found.append((topic, type_name))
        return found

    def subscribe(self, topic: str, type_name: str) -> None:
        """Subscribe to a single topic, resolving its message class at runtime."""
        if topic in self._subscriptions:
            return

        from rosidl_runtime_py.utilities import get_message

        message_class = get_message(normalize_type_name(type_name))
        preset = self.qos_for(topic)

        def callback(msg: Any, topic: str = topic, type_name: str = type_name) -> None:
            self.handle_message(topic, type_name, msg)

        self._subscriptions[topic] = self.node.create_subscription(
            message_class,
            topic,
            callback,
            qos_profile(preset, depth=self.depth),
        )

    def refresh_subscriptions(self) -> int:
        """Subscribe to every newly advertised topic. Returns how many were added."""
        added = 0
        for topic, type_name in self.discover():
            if topic not in self._subscriptions:
                self.subscribe(topic, type_name)
                added += 1
        return added

    @property
    def topics(self) -> list[str]:
        """The topics currently subscribed to."""
        return sorted(self._subscriptions)

    def spin(self, duration: float | None = None) -> None:
        """
        Spin the node, re-discovering topics as they appear.

        Parameters
        ----------
        duration:
            Stop after this many seconds. `None` spins until interrupted, which
            is what you want when driving a live robot.

        """
        import rclpy

        self.start()
        deadline = None if duration is None else time.monotonic() + duration
        next_discovery = 0.0

        try:
            while rclpy.ok():
                now = time.monotonic()
                if now >= next_discovery:
                    self.refresh_subscriptions()
                    next_discovery = now + self.discovery_period
                if deadline is not None and now >= deadline:
                    break
                rclpy.spin_once(self._node, timeout_sec=0.05)
        except KeyboardInterrupt:
            pass

    def close(self) -> None:
        """Destroy the node. Safe to call more than once, and safe without ROS."""
        if self._node is None:
            return
        node, self._node = self._node, None
        self._subscriptions.clear()
        node.destroy_node()

    def __enter__(self) -> Ros2Bridge:
        self.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Ros2Bridge(node_name={self.node_name!r}, topics={len(self._subscriptions)})"


def bridge_topics(
    topics: Iterable[tuple[str, str]],
    *,
    allow: Sequence[str] = (),
    deny: Sequence[str] = DEFAULT_DENY,
) -> list[tuple[str, str]]:
    """
    Return the subset of `(topic, type_name)` pairs a bridge would subscribe to.

    Useful for `dalaran-ros2 bridge --dry-run` and for reasoning about a bag's
    contents before replaying it.

    Examples
    --------
    ```python
    from dalaran.ros2.bridge import bridge_topics

    available = [("/scan", "sensor_msgs/msg/LaserScan"), ("/rosout", "rcl_interfaces/msg/Log")]
    assert bridge_topics(available) == [("/scan", "sensor_msgs/msg/LaserScan")]
    ```

    """
    bridge = Ros2Bridge(allow=allow, deny=deny, on_unknown_type=lambda _type_name: None)
    return [(topic, type_name) for topic, type_name in topics if bridge.accepts(topic, type_name)]
