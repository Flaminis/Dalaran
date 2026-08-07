"""Unit tests for topic routing, QoS selection, throttling and the per-message path."""

from __future__ import annotations

import pytest
from dalaran.ros2.bridge import DEFAULT_DENY, Ros2Bridge, bridge_topics
from dalaran.ros2.naming import (
    Throttler,
    TopicFilter,
    entity_path_join,
    sanitize_path_part,
    stamp_to_nanos,
    topic_to_entity_path,
)

from .fake_msgs import Simple, header

# -- naming -----------------------------------------------------------------


def test_a_topic_tree_becomes_an_entity_tree() -> None:
    assert topic_to_entity_path("/camera/color/image_raw") == "camera/color/image_raw"
    assert topic_to_entity_path("camera/color/image_raw") == "camera/color/image_raw"


def test_a_prefix_nests_a_whole_robot() -> None:
    assert topic_to_entity_path("/scan", prefix="robots/spot") == "robots/spot/scan"


def test_an_override_re_homes_a_single_topic() -> None:
    overrides = {"/scan": "world/base_link/lidar"}
    assert topic_to_entity_path("/scan", overrides=overrides) == "world/base_link/lidar"
    # Overrides are still nested under the prefix.
    assert topic_to_entity_path("/scan", prefix="a", overrides=overrides) == "a/world/base_link/lidar"


def test_awkward_topic_names_are_sanitized() -> None:
    assert sanitize_path_part("image raw!") == "image_raw_"
    assert entity_path_join("robots/spot", "", "lidar") == "robots/spot/lidar"


# -- filtering --------------------------------------------------------------


def test_an_empty_allow_list_allows_everything() -> None:
    assert TopicFilter().accepts("/anything/at/all")


def test_deny_beats_allow() -> None:
    filt = TopicFilter(allow=["/camera/*"], deny=["*/compressed*"])
    assert filt.accepts("/camera/color/image_raw")
    assert not filt.accepts("/camera/color/image_raw/compressed")
    assert not filt.accepts("/scan")


def test_filtering_preserves_order() -> None:
    filt = TopicFilter(deny=["/rosout"])
    assert filt.filter(["/scan", "/rosout", "/odom"]) == ["/scan", "/odom"]


# -- throttling -------------------------------------------------------------


def test_an_unlimited_topic_always_passes() -> None:
    throttle = Throttler()
    assert all(throttle.should_log("/imu", t / 1000.0) for t in range(10))


def test_a_rate_limit_drops_the_messages_in_between() -> None:
    throttle = Throttler(rules={"/imu": 2.0})  # 2 Hz, so one every 0.5 s
    assert throttle.should_log("/imu", 0.0)
    assert not throttle.should_log("/imu", 0.1)
    assert not throttle.should_log("/imu", 0.49)
    assert throttle.should_log("/imu", 0.5)


def test_globs_and_a_default_both_apply() -> None:
    throttle = Throttler(default=1.0, rules={"/camera/*": 10.0})
    assert throttle.rate_for("/camera/color/image_raw") == 10.0
    assert throttle.rate_for("/odom") == 1.0


def test_topics_are_throttled_independently() -> None:
    throttle = Throttler(default=1.0)
    assert throttle.should_log("/a", 0.0)
    assert throttle.should_log("/b", 0.0)
    assert not throttle.should_log("/a", 0.5)


def test_time_going_backwards_is_treated_as_a_new_bag_loop() -> None:
    throttle = Throttler(default=1.0)
    assert throttle.should_log("/scan", 100.0)
    assert throttle.should_log("/scan", 0.0)


def test_reset_forgets_everything() -> None:
    throttle = Throttler(default=1.0)
    throttle.should_log("/scan", 0.0)
    throttle.reset()
    assert throttle.should_log("/scan", 0.1)


# -- header stamps ----------------------------------------------------------


def test_a_header_stamp_becomes_nanoseconds() -> None:
    assert stamp_to_nanos(header(sec=3, nanosec=500_000_000)) == 3_500_000_000


def test_the_all_zero_stamp_means_no_time_at_all() -> None:
    # ROS publishers that forget to stamp send zeros; logging those at the epoch
    # would put every message in 1970 and ruin the timeline.
    assert stamp_to_nanos(header()) is None
    assert stamp_to_nanos(None) is None


# -- bridge routing ---------------------------------------------------------


def test_the_bridge_mirrors_the_topic_tree() -> None:
    bridge = Ros2Bridge(prefix="robots/spot")
    assert bridge.entity_path_for("/camera/image_raw") == "robots/spot/camera/image_raw"


@pytest.mark.parametrize(
    ("topic", "expected"),
    [
        ("/scan", "sensor_data"),
        ("/camera/image_raw", "sensor_data"),
        # Latched publishers send once at startup; a volatile subscription to
        # these receives absolutely nothing.
        ("/map", "transient_local"),
        ("/tf_static", "transient_local"),
        ("/robot_description", "transient_local"),
    ],
)
def test_latched_topics_get_a_transient_local_subscription(topic: str, expected: str) -> None:
    assert Ros2Bridge().qos_for(topic) == expected


def test_qos_can_be_overridden_per_topic_glob() -> None:
    bridge = Ros2Bridge(qos_overrides={"/costmap*": "transient_local", "/odom": "reliable"})
    assert bridge.qos_for("/costmap/costmap") == "transient_local"
    assert bridge.qos_for("/odom") == "reliable"


def test_topics_without_a_converter_are_not_subscribed_to() -> None:
    bridge = Ros2Bridge(on_unknown_type=lambda _name: None)
    assert bridge.accepts("/scan", "sensor_msgs/msg/LaserScan")
    assert not bridge.accepts("/whatever", "nowhere_msgs/msg/Nothing")


def test_the_default_deny_list_skips_the_noise() -> None:
    bridge = Ros2Bridge(on_unknown_type=lambda _name: None)
    assert not bridge.accepts("/rosout", "std_msgs/msg/String")
    assert not bridge.accepts("/parameter_events", "std_msgs/msg/String")
    assert "/rosout" in DEFAULT_DENY


def test_an_unknown_type_is_only_reported_once() -> None:
    seen: list[str] = []
    bridge = Ros2Bridge(on_unknown_type=seen.append)
    bridge.accepts("/a", "nowhere_msgs/msg/Nothing")
    bridge.accepts("/b", "nowhere_msgs/msg/Nothing")
    assert seen == ["nowhere_msgs/msg/Nothing"]


def test_bridge_topics_reports_what_would_be_subscribed_to() -> None:
    available = [
        ("/scan", "sensor_msgs/msg/LaserScan"),
        ("/rosout", "rcl_interfaces/msg/Log"),
        ("/tf", "tf2_msgs/msg/TFMessage"),
    ]
    assert bridge_topics(available) == [
        ("/scan", "sensor_msgs/msg/LaserScan"),
        ("/tf", "tf2_msgs/msg/TFMessage"),
    ]


# -- the per-message path ---------------------------------------------------


def _string_msg(text: str) -> Simple:
    return Simple(data=text)


def test_handle_message_converts_and_reports_success(_fake_dl, captured) -> None:
    bridge = Ros2Bridge()
    bridge.context.sink = captured

    assert bridge.handle_message("/status", "std_msgs/msg/String", _string_msg("ok"), wall_time=0.0)
    assert captured.logs[0].entity_path == "status"


def test_handle_message_returns_false_for_unknown_types(_fake_dl, captured) -> None:
    bridge = Ros2Bridge()
    bridge.context.sink = captured
    assert not bridge.handle_message("/x", "nowhere_msgs/msg/Nothing", Simple(), wall_time=0.0)


def test_handle_message_honors_the_rate_limit(_fake_dl, captured) -> None:
    bridge = Ros2Bridge(max_hz={"/status": 1.0})
    bridge.context.sink = captured

    assert bridge.handle_message("/status", "std_msgs/msg/String", _string_msg("a"), wall_time=0.0)
    assert not bridge.handle_message("/status", "std_msgs/msg/String", _string_msg("b"), wall_time=0.5)
    assert bridge.handle_message("/status", "std_msgs/msg/String", _string_msg("c"), wall_time=1.0)
    assert len(captured.logs) == 2


def test_the_rate_limit_follows_the_header_stamp_when_there_is_one(_fake_dl, captured) -> None:
    bridge = Ros2Bridge(max_hz={"/scan": 1.0})
    bridge.context.sink = captured

    def stamped(sec: int) -> Simple:
        return Simple(data="x", header=header(sec=sec))

    # Wall time barely moves, but the message stamps are a second apart, so
    # replaying a bag faster than real time still respects the requested rate.
    assert bridge.handle_message("/scan", "std_msgs/msg/String", stamped(10), wall_time=0.0)
    assert not bridge.handle_message("/scan", "std_msgs/msg/String", stamped(10), wall_time=0.001)
    assert bridge.handle_message("/scan", "std_msgs/msg/String", stamped(11), wall_time=0.002)


def test_an_unknown_qos_preset_is_rejected() -> None:
    from dalaran.ros2.bridge import qos_profile

    with pytest.raises((ValueError, ImportError, ModuleNotFoundError)):
        qos_profile("carrier_pigeon")


def test_close_is_safe_without_ros() -> None:
    bridge = Ros2Bridge()
    bridge.close()
    bridge.close()
    assert bridge.topics == []
