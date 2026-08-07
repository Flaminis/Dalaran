---
title: Visualize ROS 2 data
order: 200
description: Bridge a live ROS 2 graph or replay a rosbag2 recording with `dalaran.ros2`
---

`dalaran.ros2` turns a ROS 2 graph into a Dalaran recording. It subscribes with
`rclpy`, maps message types onto Dalaran archetypes, and puts every sensor
reading in the frame it was actually measured in by replaying `/tf` into a
[transform tree](robot-api.md).

The fastest way to see something is the command line tool:

```sh
dalaran-ros2 bridge --allow '/tf' --allow '/tf_static' --allow '/scan' --allow '/map'
```

or, from Python:

```python
import dalaran as dl
from dalaran.ros2 import Ros2Bridge

dl.init("my_robot", spawn=True)

with Ros2Bridge(
    allow=["/tf", "/tf_static", "/scan", "/odom", "/map"],
    max_hz={"/camera/*": 5.0},
) as bridge:
    bridge.spin()
```

## Installing

`dalaran.ros2` ships with the SDK and adds no dependencies:

```sh
pip install dalaran-sdk
```

The ROS packages (`rclpy`, `rosidl_runtime_py`, and the message definitions) are
imported lazily, inside the functions that need them, so `import dalaran.ros2`
works fine on a machine with no ROS installed. That is not an accident: it means
you can inspect and replay bags anywhere, and only need ROS on the machine that
talks to a live graph.

The one thing to get right is that Dalaran must be installed into the *same*
Python interpreter your ROS 2 distribution uses:

```sh
source /opt/ros/jazzy/setup.bash
python3 -m pip install dalaran-sdk
python3 -c "import rclpy, dalaran.ros2; print('ok')"
```

Installing into a virtualenv that does not inherit the ROS `site-packages` is
the most common reason `dalaran-ros2 bridge` cannot find `rclpy`.

## What is supported out of the box

| ROS 2 message | Becomes |
| --- | --- |
| `sensor_msgs/PointCloud2` | [`Points3D`](../../reference/types/archetypes/points3d.md), colored by `rgb` or colormapped by `intensity` |
| `sensor_msgs/LaserScan` | [`Points3D`](../../reference/types/archetypes/points3d.md), via `dalaran.robot.log_lidar_scan` |
| `sensor_msgs/Image` | [`Image`](../../reference/types/archetypes/image.md) or [`DepthImage`](../../reference/types/archetypes/depth_image.md) |
| `sensor_msgs/CompressedImage` | [`EncodedImage`](../../reference/types/archetypes/encoded_image.md), bytes forwarded untouched |
| `sensor_msgs/CameraInfo` | [`Pinhole`](../../reference/types/archetypes/pinhole.md) in an RDF optical frame |
| `sensor_msgs/Imu` | [`Arrows3D`](../../reference/types/archetypes/arrows3d.md) plus per-axis [`Scalars`](../../reference/types/archetypes/scalars.md) |
| `sensor_msgs/JointState` | One [`Scalars`](../../reference/types/archetypes/scalars.md) series per joint and quantity |
| `sensor_msgs/NavSatFix` | [`GeoPoints`](../../reference/types/archetypes/geo_points.md) on the map view |
| `nav_msgs/Odometry` | [`Transform3D`](../../reference/types/archetypes/transform3d.md) plus twist series |
| `nav_msgs/Path` | [`LineStrips3D`](../../reference/types/archetypes/line_strips3d.md) |
| `nav_msgs/OccupancyGrid` | [`GridMap`](../../reference/types/archetypes/grid_map.md) with the RViz map colormap |
| `nav2_msgs/Costmap`, `*/costmap` topics | Cost-colormapped [`GridMap`](../../reference/types/archetypes/grid_map.md) layers, see [costmaps](costmaps.md) |
| `geometry_msgs/PoseStamped`, `PoseArray`, `Twist` | Transforms, points with heading arrows, arrows plus series |
| `geometry_msgs/TransformStamped`, `tf2_msgs/TFMessage` | The transform tree |
| `visualization_msgs/Marker`, `MarkerArray` | Boxes, ellipsoids, cylinders, line strips, points, meshes, text |
| `std_msgs/*` | Scalars for numbers, [`TextLog`](../../reference/types/archetypes/text_log.md) for everything else |

Anything without a converter is skipped, with a one-line note naming the type so
you know what you are missing.

## Topics, entity paths and `/tf`

By default the entity tree mirrors the topic tree, so `/camera/color/image_raw`
lands on `camera/color/image_raw` and you can find things in the viewer using
the names you already know from `ros2 topic list`.

`/tf` and `/tf_static` are handled specially. Rather than being logged at their
own topic path, each transform is replayed into a
[`dalaran.robot.TransformTree`][], which turns `odom -> base_link -> base_scan`
into the entity hierarchy `odom/base_link/base_scan`. Once a frame is known,
sensor messages carrying that `frame_id` are logged onto the frame's entity
instead of the topic's, so the scan moves with the robot without you configuring
anything.

Two knobs adjust the mapping:

```python
Ros2Bridge(
    # Nest a whole robot, so two of them can share one recording.
    prefix="robots/spot",
    # Or re-home individual topics.
    topic_paths={"/scan": "world/odom/base_footprint/base_scan"},
)
```

## QoS gotchas

This is where ROS 2 bridges usually go wrong, because the failure mode is an
empty viewer rather than an error message.

* **Sensor drivers publish best effort.** A `RELIABLE` subscription to a
  `BEST_EFFORT` publisher is an incompatible match, and you receive *nothing*.
  This is why the bridge's default preset is `"sensor_data"`.
* **`/map`, `/tf_static` and `/robot_description` are latched.** They publish
  once, at startup, with `TRANSIENT_LOCAL` durability. A `VOLATILE` subscription
  that starts later also receives nothing. The bridge recognizes these topics by
  name and subscribes with `"transient_local"` automatically.
* **Costmaps and other Nav2 topics are latched too**, but under names we cannot
  guess. Say so explicitly:

  ```python
  Ros2Bridge(qos_overrides={"/*costmap*": "transient_local"})
  ```

  or, from the CLI:

  ```sh
  dalaran-ros2 bridge --qos-override '/*costmap*=transient_local'
  ```

The available presets are `"sensor_data"`, `"reliable"`, `"transient_local"` and
`"system_default"`. When a topic stays stubbornly empty, `ros2 topic info -v
<topic>` will show you the publisher's actual profile.

## Keeping the firehose under control

A 3 kHz IMU and a 30 FPS camera will bury a 1 Hz map. Rate limit per topic glob:

```python
Ros2Bridge(
    max_hz={"/camera/*": 5.0, "/imu": 50.0},
    default_max_hz=None,  # everything else is unlimited
)
```

Throttling is driven by the message's own header stamp when it has one, so a bag
replayed as fast as possible still thins out to the rate you asked for.

## Timelines

Every message lands on two timelines:

* `ros_time`, from the message's `header.stamp`. This is the one to scrub on.
* `log_time`, the bridge's own wall clock. Messages with no header, or with the
  all-zero stamp that unstamped publishers send, only appear here - which is
  much better than logging them at the 1970 epoch.

## Replaying a rosbag2 recording

```sh
# Look inside a bag. Needs no ROS at all.
dalaran-ros2 info my_bag

# Replay it into a recording file.
dalaran-ros2 bag my_bag --save my_bag.dlr

# Or watch it happen in real time.
dalaran-ros2 bag my_bag --speed 1.0
```

`sqlite3` bags are read with the standard library, so listing a bag's topics,
types, message counts and duration works on any machine. Deserializing the
messages needs the message definitions, so that part still wants ROS - unless
the bag is `.mcap` and `mcap_ros2` is installed, in which case even that works
without ROS, because MCAP embeds the schemas.

From Python:

```python
import dalaran as dl
from dalaran.ros2 import Ros2Bridge
from dalaran.ros2.bag import replay_bag

dl.init("my_bag", spawn=True)
replay_bag("my_bag", Ros2Bridge(allow=["/tf", "/tf_static", "/scan", "/map"]))
```

## Custom messages

Every robotics project has its own interfaces, and Dalaran does not need to know
about them in advance. Register a converter and your message type becomes a
first-class citizen of the live bridge, the bag replayer and the CLI, all at
once:

```python
import dalaran as dl
from dalaran.ros2 import register


@register("my_pkg/msg/BatteryPack")
def log_battery_pack(msg, entity_path, ctx):
    """Log a battery pack: a state of charge series and one series per cell."""
    ctx.log(f"{entity_path}/state_of_charge", dl.Scalars(float(msg.state_of_charge)))
    for index, voltage in enumerate(msg.cell_voltages):
        ctx.log(f"{entity_path}/cells/{index}", dl.Scalars(float(voltage)))
```

The contract is small:

* The function takes `(msg, entity_path, ctx)` and returns `None`.
* `entity_path` is where the topic mapped to; build sub-paths below it.
* `ctx` is a [`dalaran.ros2.Context`][]. Log through `ctx.log(path, *archetypes,
  static=False)` rather than [`dalaran.log`][] so your converter honors the
  caller's recording and stays unit-testable.
* Type names are accepted in every spelling: `"my_pkg/BatteryPack"`,
  `"my_pkg/msg/BatteryPack"` and `"my_pkg.msg.BatteryPack"` are the same entry.

A few more things you can do:

```python
# One converter for several types.
@register("my_pkg/msg/Foo", "my_pkg/msg/Bar")
def log_foo_or_bar(msg, entity_path, ctx): ...


# A whole package at once, via the wildcard entry.
@register("my_pkg/msg/*")
def log_anything_from_my_pkg(msg, entity_path, ctx): ...


# Replace a built-in, deliberately. Without `override=True` this raises, so a
# typo cannot silently disable a message type.
@register("sensor_msgs/msg/Imu", override=True)
def log_imu_my_way(msg, entity_path, ctx): ...
```

For the converter to be picked up, the module defining it has to be imported
before the bridge runs. In a script that is automatic; with the CLI, import your
package first:

```sh
python -c "import my_pkg.dalaran_converters; from dalaran.ros2.cli import main; main()" bridge
```

### Testing a custom converter

Converters log through the context, so a test can capture their output without a
viewer, a recording, or even a ROS installation:

```python
from dalaran.ros2 import convert
from dalaran.ros2.context import Context


def test_battery_pack_logs_every_cell():
    captured = []
    ctx = Context(sink=captured.append)

    convert("my_pkg/msg/BatteryPack", my_message, "battery", ctx)

    assert [record.entity_path for record in captured] == [
        "battery/state_of_charge",
        "battery/cells/0",
        "battery/cells/1",
    ]
```

## Working with the raw data yourself

The decoding helpers are plain functions over numpy arrays, usable on their own:

```python
from dalaran.ros2.pointcloud2 import decode_pointcloud2
from dalaran.ros2.occupancy_grid import occupancy_grid_placement

cloud = decode_pointcloud2(msg)  # positions, intensity, colors, ring, times
placement = occupancy_grid_placement(
    grid.data,
    width=grid.info.width,
    height=grid.info.height,
    resolution=grid.info.resolution,
)
```

`decode_pointcloud2` builds a numpy structured dtype from the message's own
`fields` and `point_step` and views the buffer through it, so Velodyne, Ouster,
Livox and RGB-D layouts all work without copying and without driver-specific
code.

## Related

* [Log a robot with the high-level robot API](robot-api.md) - the transform tree
  and sensor conventions the bridge builds on.
* [Visualize nav2 costmaps](costmaps.md) - cost semantics, layered costmaps and
  the rolling local window.
* [`GridMap`](../../reference/types/archetypes/grid_map.md) - the occupancy grid
  and costmap archetype.
