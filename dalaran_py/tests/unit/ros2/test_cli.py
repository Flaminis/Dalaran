"""Unit tests for the `dalaran-ros2` command line tool."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from dalaran.ros2 import cli

from .test_bag import write_bag

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def bag(tmp_path: Path) -> Path:
    write_bag(tmp_path / "my_bag")
    return tmp_path / "my_bag"


def test_a_subcommand_is_required() -> None:
    with pytest.raises(SystemExit):
        cli.main([])


def test_info_lists_topics_types_and_counts(bag: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # `info` deliberately needs no ROS at all, so it works on any machine.
    assert cli.main(["info", str(bag)]) == 0
    out = capsys.readouterr().out
    assert "/scan" in out
    assert "sensor_msgs/msg/LaserScan" in out
    assert "2 msgs" in out
    assert "duration: 2.000 s" in out


def test_info_on_a_missing_bag_fails_cleanly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["info", str(tmp_path / "nope")]) == 1
    assert "dalaran-ros2:" in capsys.readouterr().err


def test_rate_limits_are_parsed_as_topic_equals_hz() -> None:
    assert cli._parse_rate("/camera/*=5") == ("/camera/*", 5.0)
    with pytest.raises(Exception, match=r"Hz|number"):
        cli._parse_rate("/camera/*=fast")
    with pytest.raises(Exception, match="TOPIC=HZ"):
        cli._parse_rate("/camera/*")


def test_entity_path_overrides_are_parsed_as_key_equals_value() -> None:
    assert cli._parse_mapping("/scan=world/base_link/lidar") == ("/scan", "world/base_link/lidar")
    with pytest.raises(Exception, match="KEY=VALUE"):
        cli._parse_mapping("/scan")


def test_bridge_arguments_build_the_bridge_they_describe() -> None:
    args = cli._parser().parse_args([
        "bridge",
        "--allow",
        "/scan",
        "--allow",
        "/tf",
        "--deny",
        "/rosout",
        "--max-hz",
        "/camera/*=5",
        "--prefix",
        "robots/spot",
        "--entity-path",
        "/scan=world/base_link/lidar",
        "--qos-override",
        "/costmap*=transient_local",
    ])
    bridge = cli._make_bridge(args)

    assert bridge.filter.accepts("/scan")
    assert not bridge.filter.accepts("/rosout")
    assert bridge.throttler.rate_for("/camera/color/image_raw") == 5.0
    assert bridge.entity_path_for("/scan") == "robots/spot/world/base_link/lidar"
    assert bridge.qos_for("/costmap/costmap") == "transient_local"


def test_an_invalid_qos_preset_is_rejected_at_parse_time() -> None:
    with pytest.raises(SystemExit):
        cli._parser().parse_args(["bridge", "--qos", "carrier_pigeon"])


def test_bag_replay_defaults_to_as_fast_as_possible() -> None:
    args = cli._parser().parse_args(["bag", "my_bag"])
    assert args.speed == 0.0
    assert args.path == "my_bag"
