"""
Offline replay of rosbag2 recordings into Dalaran.

A rosbag2 `sqlite3` bag is a directory containing a `metadata.yaml` and one or
more `.db3` files, and the `.db3` schema is two tables: `topics` (name, type)
and `messages` (topic_id, nanosecond timestamp, CDR blob). Reading that needs
nothing but the standard library, so this module implements it directly rather
than requiring a ROS installation just to enumerate a bag.

Deserializing the CDR blobs *does* need the message definitions, so that step
imports `rclpy` lazily. The practical consequence is useful: you can inspect a
bag's topics, types, message counts and time range anywhere, and you only need
ROS on the machine that actually visualizes it. `.mcap` bags are read through
`mcap_ros2` when it is installed - which decodes without ROS, because MCAP
embeds the message schemas - and otherwise through `rosbag2_py`.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .msg_map import normalize_type_name

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from .bridge import Ros2Bridge

__all__ = [
    "BagMessage",
    "Rosbag2Reader",
    "SqliteBagReader",
    "deserialize",
    "open_bag",
    "replay_bag",
]


@dataclass(frozen=True)
class BagMessage:
    """
    One serialized message read out of a bag.

    Attributes
    ----------
    topic:
        The topic the message was published on.
    type_name:
        The canonical `pkg/msg/Type` name.
    timestamp_ns:
        The bag's receive timestamp, in nanoseconds since the epoch.
    raw:
        The serialized message. `bytes` for a sqlite3 bag, or an already
        deserialized message object when the backend decoded it for us.
    deserialized:
        Whether `raw` is already a message object rather than bytes.

    """

    topic: str
    type_name: str
    timestamp_ns: int
    raw: Any
    deserialized: bool = False


class Rosbag2Reader:
    """Base class for the bag backends, so callers can treat them alike."""

    #: `topic name -> pkg/msg/Type`.
    topics: dict[str, str]

    def messages(self, topics: Sequence[str] | None = None) -> Iterator[BagMessage]:
        """Yield every message in the bag, in timestamp order."""
        raise NotImplementedError

    def close(self) -> None:
        """Release any resources the backend holds."""

    def __enter__(self) -> Rosbag2Reader:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


class SqliteBagReader(Rosbag2Reader):
    """
    Read a rosbag2 `sqlite3` bag with nothing but the standard library.

    Parameters
    ----------
    path:
        A bag directory, or a single `.db3` file.

    Examples
    --------
    ```python
    from dalaran.ros2.bag import SqliteBagReader

    with SqliteBagReader("my_bag") as reader:
        print(reader.topics)
        print(reader.message_counts())
    ```

    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._files = self._find_db3_files(self.path)
        if not self._files:
            msg = f"No rosbag2 sqlite3 (.db3) files found in {self.path}"
            raise FileNotFoundError(msg)

        self.topics: dict[str, str] = {}
        # `topic_id` is per file, so keep one table per file.
        self._topic_ids: list[dict[int, str]] = []
        for file in self._files:
            ids: dict[int, str] = {}
            with self._connect(file) as connection:
                for topic_id, name, type_name in connection.execute("SELECT id, name, type FROM topics"):
                    canonical = normalize_type_name(str(type_name))
                    ids[int(topic_id)] = str(name)
                    self.topics[str(name)] = canonical
            self._topic_ids.append(ids)

    @staticmethod
    def _find_db3_files(path: Path) -> list[Path]:
        if path.is_file():
            return [path]
        return sorted(path.glob("*.db3"))

    @staticmethod
    def _connect(file: Path) -> sqlite3.Connection:
        # Read-only, so a bag that is still being recorded is never disturbed.
        return sqlite3.connect(f"file:{file}?mode=ro", uri=True)

    def message_counts(self) -> dict[str, int]:
        """
        Return the number of messages per topic.

        Examples
        --------
        ```python
        from dalaran.ros2.bag import SqliteBagReader

        with SqliteBagReader("my_bag") as reader:
            for topic, count in sorted(reader.message_counts().items()):
                print(f"{count:>8}  {topic}")
        ```

        """
        counts: dict[str, int] = dict.fromkeys(self.topics, 0)
        for file, ids in zip(self._files, self._topic_ids, strict=False):
            with self._connect(file) as connection:
                for topic_id, count in connection.execute("SELECT topic_id, COUNT(*) FROM messages GROUP BY topic_id"):
                    topic = ids.get(int(topic_id))
                    if topic is not None:
                        counts[topic] = counts.get(topic, 0) + int(count)
        return counts

    def time_range(self) -> tuple[int, int] | None:
        """Return the bag's `(first, last)` timestamps in nanoseconds, or `None` if it is empty."""
        lows: list[int] = []
        highs: list[int] = []
        for file in self._files:
            with self._connect(file) as connection:
                low, high = next(iter(connection.execute("SELECT MIN(timestamp), MAX(timestamp) FROM messages")))
                if low is not None:
                    lows.append(int(low))
                    highs.append(int(high))
        return (min(lows), max(highs)) if lows else None

    def messages(self, topics: Sequence[str] | None = None) -> Iterator[BagMessage]:
        """Yield the bag's messages in timestamp order, still CDR-serialized."""
        wanted = set(topics) if topics is not None else None
        for file, ids in zip(self._files, self._topic_ids, strict=False):
            with self._connect(file) as connection:
                rows = connection.execute("SELECT topic_id, timestamp, data FROM messages ORDER BY timestamp")
                for topic_id, timestamp, data in rows:
                    topic = ids.get(int(topic_id))
                    if topic is None or (wanted is not None and topic not in wanted):
                        continue
                    yield BagMessage(topic, self.topics[topic], int(timestamp), bytes(data))


class McapBagReader(Rosbag2Reader):
    """
    Read an `.mcap` bag through the `mcap_ros2` package.

    MCAP embeds the message schemas, so this backend deserializes without a ROS
    installation - which makes it the nicest way to look at somebody else's bag.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._files = [self.path] if self.path.is_file() else sorted(self.path.glob("*.mcap"))
        if not self._files:
            msg = f"No MCAP (.mcap) files found in {self.path}"
            raise FileNotFoundError(msg)

        # The channel/schema tables live in the file summary, so listing topics
        # does not require walking the messages.
        from mcap.reader import make_reader

        self.topics = {}
        for file in self._files:
            with file.open("rb") as handle:
                summary = make_reader(handle).get_summary()
            if summary is None:
                continue
            for channel in summary.channels.values():
                schema = summary.schemas.get(channel.schema_id)
                if schema is not None:
                    self.topics[channel.topic] = normalize_type_name(schema.name)

    def messages(self, topics: Sequence[str] | None = None) -> Iterator[BagMessage]:
        """Yield already-deserialized messages in the order MCAP stores them."""
        from mcap_ros2.reader import read_ros2_messages

        wanted = list(topics) if topics is not None else None
        for file in self._files:
            for message in read_ros2_messages(str(file), topics=wanted):
                type_name = self.topics.get(message.channel.topic)
                if type_name is None:
                    type_name = normalize_type_name(message.schema.name)
                yield BagMessage(
                    message.channel.topic,
                    type_name,
                    int(message.log_time_ns),
                    message.ros_msg,
                    deserialized=True,
                )


class Rosbag2PyReader(Rosbag2Reader):
    """
    Read any bag `rosbag2_py` can open, which is the authoritative fallback.

    Used when a bag uses a storage plugin we do not implement ourselves, and it
    requires a working ROS 2 installation.
    """

    def __init__(self, path: str | Path, *, storage_id: str = "") -> None:
        import rosbag2_py

        self.path = Path(path)
        self._reader = rosbag2_py.SequentialReader()
        self._reader.open(
            rosbag2_py.StorageOptions(uri=str(self.path), storage_id=storage_id),
            rosbag2_py.ConverterOptions(input_serialization_format="cdr", output_serialization_format="cdr"),
        )
        self.topics = {
            metadata.name: normalize_type_name(metadata.type) for metadata in self._reader.get_all_topics_and_types()
        }

    def messages(self, topics: Sequence[str] | None = None) -> Iterator[BagMessage]:
        """Yield the bag's messages, still CDR-serialized."""
        wanted = set(topics) if topics is not None else None
        while self._reader.has_next():
            topic, data, timestamp = self._reader.read_next()
            if wanted is not None and topic not in wanted:
                continue
            yield BagMessage(topic, self.topics[topic], int(timestamp), bytes(data))


def open_bag(path: str | Path, *, storage_id: str = "") -> Rosbag2Reader:
    """
    Open a rosbag2 recording with the most capable backend available.

    Preference order: our own sqlite3 reader (no ROS needed), `mcap_ros2` (no ROS
    needed), then `rosbag2_py` (needs ROS, but reads everything).

    Parameters
    ----------
    path:
        A bag directory, a `.db3` file or an `.mcap` file.
    storage_id:
        Forced `rosbag2_py` storage plugin, e.g. `"mcap"`. Implies the
        `rosbag2_py` backend.

    Returns
    -------
    Rosbag2Reader
        A reader for the bag.

    Examples
    --------
    ```python
    from dalaran.ros2.bag import open_bag

    with open_bag("my_bag") as reader:
        for topic, type_name in sorted(reader.topics.items()):
            print(f"{topic}  [{type_name}]")
    ```

    """
    path = Path(path)
    if storage_id:
        return Rosbag2PyReader(path, storage_id=storage_id)

    has_sqlite = path.suffix == ".db3" or (path.is_dir() and any(path.glob("*.db3")))
    if has_sqlite:
        return SqliteBagReader(path)

    has_mcap = path.suffix == ".mcap" or (path.is_dir() and any(path.glob("*.mcap")))
    if has_mcap:
        try:
            return McapBagReader(path)
        except ImportError:
            return Rosbag2PyReader(path, storage_id="mcap")

    if not path.exists():
        msg = f"No such rosbag2 recording: {path}"
        raise FileNotFoundError(msg)

    # An unfamiliar storage plugin; let rosbag2_py have a go at it.
    return Rosbag2PyReader(path)


def deserialize(message: BagMessage) -> Any:
    """
    Deserialize a [`BagMessage`][dalaran.ros2.bag.BagMessage], importing `rclpy` lazily.

    Backends that already decoded the message (MCAP) return it untouched, so this
    is safe to call unconditionally.
    """
    if message.deserialized:
        return message.raw

    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message

    return deserialize_message(message.raw, get_message(message.type_name))


def replay_bag(
    path: str | Path,
    bridge: Ros2Bridge,
    *,
    speed: float = 0.0,
    storage_id: str = "",
    progress: Any = None,
) -> int:
    """
    Replay a rosbag2 recording through a bridge's converter pipeline.

    The bridge is reused rather than reimplemented, so a bag looks exactly like
    the live robot did: same entity paths, same QoS-independent routing, same
    throttling, same custom converters.

    Parameters
    ----------
    path:
        The bag to replay.
    bridge:
        A configured [`Ros2Bridge`][dalaran.ros2.Ros2Bridge]. Its `rclpy` side is
        never touched; only its routing and conversion are used.
    speed:
        Replay speed multiplier. `0` (the default) replays as fast as possible,
        which is what you want when producing a recording. `1.0` replays in real
        time, which is what you want when watching it happen.
    storage_id:
        Forced `rosbag2_py` storage plugin.
    progress:
        Optional callable invoked with each converted
        [`BagMessage`][dalaran.ros2.bag.BagMessage].

    Returns
    -------
    int
        How many messages were converted and logged.

    Examples
    --------
    ```python
    import dalaran as dl
    from dalaran.ros2 import Ros2Bridge
    from dalaran.ros2.bag import replay_bag

    dl.init("dalaran_example_ros2_bag", spawn=True)
    replay_bag("my_bag", Ros2Bridge(allow=["/tf", "/tf_static", "/scan", "/map"]))
    ```

    """
    logged = 0
    with open_bag(path, storage_id=storage_id) as reader:
        wanted = [topic for topic, type_name in reader.topics.items() if bridge.accepts(topic, type_name)]
        if not wanted:
            return 0

        started_wall = time.monotonic()
        started_bag: int | None = None

        for message in reader.messages(wanted):
            if started_bag is None:
                started_bag = message.timestamp_ns
            if speed > 0.0:
                target = (message.timestamp_ns - started_bag) * 1e-9 / speed
                delay = target - (time.monotonic() - started_wall)
                if delay > 0.0:
                    time.sleep(delay)

            if bridge.handle_message(
                message.topic,
                message.type_name,
                deserialize(message),
                wall_time=message.timestamp_ns * 1e-9,
            ):
                logged += 1
                if progress is not None:
                    progress(message)

    return logged
