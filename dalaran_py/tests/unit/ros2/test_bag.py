"""Unit tests for the standard-library rosbag2 sqlite3 reader."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest
from dalaran.ros2.bag import BagMessage, SqliteBagReader, open_bag, replay_bag
from dalaran.ros2.bridge import Ros2Bridge

if TYPE_CHECKING:
    from pathlib import Path

TOPICS = [
    (1, "/scan", "sensor_msgs/msg/LaserScan"),
    (2, "/rosout", "rcl_interfaces/msg/Log"),
    (3, "/status", "std_msgs/msg/String"),
]


def write_bag(directory: Path, name: str = "bag_0.db3", messages: list[tuple[int, int, bytes]] | None = None) -> Path:
    """Write a minimal rosbag2 sqlite3 file with the real schema."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name

    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE topics ("
            "id INTEGER PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL, "
            "serialization_format TEXT NOT NULL, offered_qos_profiles TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE messages ("
            "id INTEGER PRIMARY KEY, topic_id INTEGER NOT NULL, "
            "timestamp INTEGER NOT NULL, data BLOB NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO topics VALUES (?, ?, ?, 'cdr', '')",
            TOPICS,
        )
        if messages is None:
            messages = [
                (1, 2_000_000_000, b"scan-b"),
                (1, 1_000_000_000, b"scan-a"),
                (2, 1_500_000_000, b"log"),
                (3, 3_000_000_000, b"status"),
            ]
        connection.executemany(
            "INSERT INTO messages (topic_id, timestamp, data) VALUES (?, ?, ?)",
            messages,
        )
        connection.commit()
    finally:
        connection.close()

    # rosbag2 always writes this next to the .db3; we do not need it, but a real
    # bag has one, so the fixture should too.
    (directory / "metadata.yaml").write_text("rosbag2_bagfile_information:\n  storage_identifier: sqlite3\n")
    return path


@pytest.fixture
def bag(tmp_path: Path) -> Path:
    write_bag(tmp_path / "my_bag")
    return tmp_path / "my_bag"


def test_topics_and_types_are_read_from_the_bag(bag: Path) -> None:
    with SqliteBagReader(bag) as reader:
        assert reader.topics == {
            "/scan": "sensor_msgs/msg/LaserScan",
            "/rosout": "rcl_interfaces/msg/Log",
            "/status": "std_msgs/msg/String",
        }


def test_a_single_db3_file_can_be_opened_directly(bag: Path) -> None:
    with SqliteBagReader(bag / "bag_0.db3") as reader:
        assert "/scan" in reader.topics


def test_messages_come_out_in_timestamp_order(bag: Path) -> None:
    with SqliteBagReader(bag) as reader:
        stamps = [message.timestamp_ns for message in reader.messages()]
    assert stamps == sorted(stamps)


def test_messages_can_be_restricted_to_some_topics(bag: Path) -> None:
    with SqliteBagReader(bag) as reader:
        messages = list(reader.messages(["/scan"]))
    assert [message.raw for message in messages] == [b"scan-a", b"scan-b"]
    assert {message.type_name for message in messages} == {"sensor_msgs/msg/LaserScan"}


def test_message_counts_and_time_range(bag: Path) -> None:
    with SqliteBagReader(bag) as reader:
        assert reader.message_counts() == {"/scan": 2, "/rosout": 1, "/status": 1}
        assert reader.time_range() == (1_000_000_000, 3_000_000_000)


def test_an_empty_bag_has_no_time_range(tmp_path: Path) -> None:
    write_bag(tmp_path / "empty", messages=[])
    with SqliteBagReader(tmp_path / "empty") as reader:
        assert reader.time_range() is None
        assert reader.message_counts() == {"/scan": 0, "/rosout": 0, "/status": 0}


def test_split_bags_are_read_as_one(tmp_path: Path) -> None:
    directory = tmp_path / "split"
    write_bag(directory, "bag_0.db3", messages=[(1, 1_000_000_000, b"a")])
    write_bag(directory, "bag_1.db3", messages=[(1, 2_000_000_000, b"b")])
    with SqliteBagReader(directory) as reader:
        assert [message.raw for message in reader.messages()] == [b"a", b"b"]


def test_open_bag_picks_the_sqlite_backend(bag: Path) -> None:
    with open_bag(bag) as reader:
        assert isinstance(reader, SqliteBagReader)


def test_open_bag_reports_a_missing_recording(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        open_bag(tmp_path / "not_a_bag")


def test_a_directory_without_db3_files_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "hollow").mkdir()
    with pytest.raises(FileNotFoundError, match="db3"):
        SqliteBagReader(tmp_path / "hollow")


def test_replay_skips_topics_with_no_converter(bag: Path, _fake_dl, captured, monkeypatch) -> None:
    # `/rosout` has no converter and `/scan` needs a real CDR decoder, so replay
    # only the topic we can decode here, with deserialization stubbed out.
    from dalaran.ros2 import bag as bag_module

    monkeypatch.setattr(bag_module, "deserialize", lambda message: _StringMsg(message.raw.decode()))

    bridge = Ros2Bridge(allow=["/status"], on_unknown_type=lambda _name: None)
    bridge.context.sink = captured

    assert replay_bag(bag, bridge) == 1
    assert captured.logs[0].entity_path == "status"


def test_replay_of_an_all_denied_bag_does_nothing(bag: Path, _fake_dl, captured) -> None:
    bridge = Ros2Bridge(allow=["/nothing_here"], on_unknown_type=lambda _name: None)
    bridge.context.sink = captured
    assert replay_bag(bag, bridge) == 0
    assert captured.logs == []


def test_bag_message_is_plain_data() -> None:
    message = BagMessage("/scan", "sensor_msgs/msg/LaserScan", 1, b"x")
    assert message.deserialized is False
    assert message.timestamp_ns == 1


class _StringMsg:
    def __init__(self, data: str) -> None:
        self.data = data
