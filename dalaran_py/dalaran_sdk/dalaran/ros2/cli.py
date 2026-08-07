"""
The `dalaran-ros2` command line tool.

Two subcommands, matching the two ways people actually work with ROS 2 data:

```
dalaran-ros2 bridge --allow '/tf' --allow '/scan' --allow '/map'
dalaran-ros2 bag my_recording --save my_recording.dlr
```

Plus `dalaran-ros2 info` to look inside a bag, which works without any ROS
installation at all because the sqlite3 reader is pure standard library.
"""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING, Sequence

from .bridge import DEFAULT_DENY, QOS_PRESETS, Ros2Bridge

if TYPE_CHECKING:
    from .bag import Rosbag2Reader

__all__ = ["main"]


def _parse_rate(text: str) -> tuple[str, float]:
    """Parse a `TOPIC=HZ` rate limit."""
    topic, _, rate = text.partition("=")
    if not rate:
        msg = f"Expected TOPIC=HZ, got {text!r}"
        raise argparse.ArgumentTypeError(msg)
    try:
        return topic, float(rate)
    except ValueError:
        msg = f"{rate!r} is not a number of Hz"
        raise argparse.ArgumentTypeError(msg) from None


def _parse_mapping(text: str) -> tuple[str, str]:
    """Parse a `KEY=VALUE` pair."""
    key, _, value = text.partition("=")
    if not value:
        msg = f"Expected KEY=VALUE, got {text!r}"
        raise argparse.ArgumentTypeError(msg)
    return key, value


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="GLOB",
        help="Only handle topics matching this glob. Repeatable. Default: everything with a converter.",
    )
    parser.add_argument(
        "--deny",
        action="append",
        default=[],
        metavar="GLOB",
        help=f"Skip topics matching this glob. Repeatable. Default: {' '.join(DEFAULT_DENY)}",
    )
    parser.add_argument(
        "--max-hz",
        action="append",
        default=[],
        type=_parse_rate,
        metavar="GLOB=HZ",
        help="Rate limit for topics matching a glob, e.g. '/camera/*=5'. Repeatable.",
    )
    parser.add_argument("--default-max-hz", type=float, default=None, help="Rate limit for all other topics.")
    parser.add_argument("--prefix", default="", help="Entity path prefix, e.g. 'robots/spot'.")
    parser.add_argument(
        "--entity-path",
        action="append",
        default=[],
        type=_parse_mapping,
        metavar="TOPIC=PATH",
        help="Log a topic to an explicit entity path instead of the topic-derived one. Repeatable.",
    )
    parser.add_argument("--application-id", default="dalaran_ros2", help="Recording application id.")
    parser.add_argument("--save", metavar="PATH.dlr", help="Write a recording file instead of spawning a viewer.")
    parser.add_argument("--connect", metavar="URL", help="Stream to an already running viewer at this gRPC URL.")
    parser.add_argument("--serve", action="store_true", help="Serve the recording over the web viewer.")


def _make_bridge(args: argparse.Namespace) -> Ros2Bridge:
    return Ros2Bridge(
        allow=args.allow,
        deny=args.deny or DEFAULT_DENY,
        max_hz=dict(args.max_hz),
        default_max_hz=args.default_max_hz,
        prefix=args.prefix,
        topic_paths=dict(args.entity_path),
        qos=getattr(args, "qos", "sensor_data"),
        qos_overrides=dict(getattr(args, "qos_override", []) or []),
        on_unknown_type=lambda type_name: print(f"skipping {type_name}: no converter registered", file=sys.stderr),
    )


def _init_recording(args: argparse.Namespace) -> None:
    """Start the recording the way the user asked for it."""
    import dalaran as dl

    dl.init(args.application_id, spawn=not (args.save or args.connect or args.serve))
    if args.save:
        dl.save(args.save)
    elif args.connect:
        dl.connect_grpc(args.connect)
    elif args.serve:
        dl.serve_grpc()


def _cmd_bridge(args: argparse.Namespace) -> int:
    _init_recording(args)
    bridge = _make_bridge(args)
    with bridge:
        print(f"dalaran-ros2: bridging as node {bridge.node_name!r}; press Ctrl-C to stop", file=sys.stderr)
        bridge.spin(duration=args.duration)
        print(f"dalaran-ros2: bridged {len(bridge.topics)} topic(s)", file=sys.stderr)
    return 0


def _cmd_bag(args: argparse.Namespace) -> int:
    from .bag import replay_bag

    _init_recording(args)
    bridge = _make_bridge(args)
    logged = replay_bag(args.path, bridge, speed=args.speed, storage_id=args.storage_id)
    print(f"dalaran-ros2: replayed {logged} message(s) from {args.path}", file=sys.stderr)
    return 0 if logged else 1


def _format_info(reader: Rosbag2Reader) -> str:
    lines = []
    counts = reader.message_counts() if hasattr(reader, "message_counts") else {}
    span = reader.time_range() if hasattr(reader, "time_range") else None
    if span is not None:
        lines.append(f"duration: {(span[1] - span[0]) * 1e-9:.3f} s")
    width = max((len(topic) for topic in reader.topics), default=0)
    for topic, type_name in sorted(reader.topics.items()):
        count = counts.get(topic)
        suffix = f"  [{count} msgs]" if count is not None else ""
        lines.append(f"  {topic:<{width}}  {type_name}{suffix}")
    return "\n".join(lines)


def _cmd_info(args: argparse.Namespace) -> int:
    from .bag import open_bag

    with open_bag(args.path, storage_id=args.storage_id) as reader:
        print(_format_info(reader))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dalaran-ros2",
        description="Visualize ROS 2 data with Dalaran, live or from a rosbag2 recording.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    bridge = subparsers.add_parser("bridge", help="Subscribe to a live ROS 2 graph and stream it into Dalaran.")
    _add_common_arguments(bridge)
    bridge.add_argument(
        "--qos",
        default="sensor_data",
        choices=QOS_PRESETS,
        help="Default QoS preset. Sensor drivers publish best effort, hence the default.",
    )
    bridge.add_argument(
        "--qos-override",
        action="append",
        default=[],
        type=_parse_mapping,
        metavar="GLOB=PRESET",
        help="QoS preset for topics matching a glob, e.g. '/costmap*=transient_local'. Repeatable.",
    )
    bridge.add_argument("--duration", type=float, default=None, help="Stop after this many seconds.")
    bridge.set_defaults(func=_cmd_bridge)

    bag = subparsers.add_parser("bag", help="Replay a rosbag2 recording into Dalaran.")
    bag.add_argument("path", help="Bag directory, .db3 file or .mcap file.")
    _add_common_arguments(bag)
    bag.add_argument(
        "--speed",
        type=float,
        default=0.0,
        help="Replay speed multiplier. 0 (the default) is as fast as possible; 1 is real time.",
    )
    bag.add_argument("--storage-id", default="", help="Force a rosbag2_py storage plugin, e.g. 'mcap'.")
    bag.set_defaults(func=_cmd_bag)

    info = subparsers.add_parser("info", help="List a bag's topics, types and message counts. Needs no ROS.")
    info.add_argument("path", help="Bag directory, .db3 file or .mcap file.")
    info.add_argument("--storage-id", default="", help="Force a rosbag2_py storage plugin, e.g. 'mcap'.")
    info.set_defaults(func=_cmd_info)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """
    Entry point of the `dalaran-ros2` console script.

    Examples
    --------
    ```python
    from dalaran.ros2.cli import main

    raise SystemExit(main(["info", "my_bag"]))
    ```

    """
    args = _parser().parse_args(argv)
    try:
        return int(args.func(args))
    except FileNotFoundError as err:
        print(f"dalaran-ros2: {err}", file=sys.stderr)
        return 1
    except ImportError as err:
        print(
            f"dalaran-ros2: {err}\n"
            "This subcommand needs a working ROS 2 installation; "
            "source your setup.bash, or use `dalaran-ros2 info`, which does not.",
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
