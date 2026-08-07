"""
`dalaran.ros2`: first-class ROS 2 support for Dalaran.

Point `Dalaran` at a running ROS 2 graph or at a rosbag2 recording and get a
live, correctly framed 3D visualization, without writing a bespoke bridge node
for every project.

* [`Ros2Bridge`][dalaran.ros2.Ros2Bridge] subscribes to topics with `rclpy` and
  streams them into a recording, with QoS presets, topic allow/deny globs and
  per-topic rate limits.
* [`msg_map`][dalaran.ros2.msg_map] maps ROS message types onto Dalaran
  archetypes, and is *extensible*: decorate your own function with
  [`@register("my_pkg/msg/Foo")`][dalaran.ros2.register] and your custom message
  becomes a first-class citizen of the bridge, the bag replayer and the CLI.
* [`pointcloud2`][dalaran.ros2.pointcloud2] decodes `sensor_msgs/PointCloud2`
  through a numpy structured-dtype view over the raw buffer, so Velodyne, Ouster,
  Livox and RGB-D layouts all work with no copying and no driver-specific code.
* [`occupancy_grid`][dalaran.ros2.occupancy_grid] places `nav_msgs/OccupancyGrid`
  into the map frame as a native [`dalaran.GridMap`][].
* [`costmap`][dalaran.ros2.costmap] renders nav2 costmaps with the reserved
  `INSCRIBED_INFLATED_OBSTACLE`, `LETHAL_OBSTACLE` and `NO_INFORMATION` values
  drawn distinctly, and stacks a costmap's layers as separate, ordered grid maps.

Nothing in this package imports `rclpy` at module scope, so `import dalaran.ros2`
works on a machine with no ROS installed; the ROS dependencies are pulled in
lazily by the functions that actually need them.

Examples
--------
```python
import dalaran as dl
from dalaran.ros2 import Ros2Bridge

dl.init("dalaran_example_ros2_bridge", spawn=True)

bridge = Ros2Bridge(
    allow=["/tf", "/tf_static", "/scan", "/camera/*", "/map"],
    deny=["*/theora", "*/compressedDepth"],
    max_hz={"/camera/*": 10.0},
)
bridge.spin()
```

"""

from __future__ import annotations

from . import (
    costmap as costmap,
    msg_map as msg_map,
    naming as naming,
    occupancy_grid as occupancy_grid,
    pointcloud2 as pointcloud2,
)
from .bridge import (
    DEFAULT_DENY as DEFAULT_DENY,
    QOS_PRESETS as QOS_PRESETS,
    Ros2Bridge as Ros2Bridge,
    bridge_topics as bridge_topics,
)
from .context import Context as Context
from .costmap import (
    CostmapLayer as CostmapLayer,
    RollingCostmapWindow as RollingCostmapWindow,
    costmap_to_rgba as costmap_to_rgba,
    log_costmap_layers as log_costmap_layers,
)
from .msg_map import (
    convert as convert,
    lookup as lookup,
    lookup_topic as lookup_topic,
    normalize_type_name as normalize_type_name,
    register as register,
    register_topic as register_topic,
    registered_topics as registered_topics,
    registered_types as registered_types,
)
from .naming import (
    Throttler as Throttler,
    TopicFilter as TopicFilter,
    topic_to_entity_path as topic_to_entity_path,
)
from .occupancy_grid import occupancy_grid_placement as occupancy_grid_placement
from .pointcloud2 import decode_pointcloud2 as decode_pointcloud2

__all__ = [
    "DEFAULT_DENY",
    "QOS_PRESETS",
    "Context",
    "CostmapLayer",
    "RollingCostmapWindow",
    "Ros2Bridge",
    "Throttler",
    "TopicFilter",
    "bridge_topics",
    "convert",
    "costmap",
    "costmap_to_rgba",
    "decode_pointcloud2",
    "log_costmap_layers",
    "lookup",
    "lookup_topic",
    "msg_map",
    "naming",
    "normalize_type_name",
    "occupancy_grid",
    "occupancy_grid_placement",
    "pointcloud2",
    "register",
    "register_topic",
    "registered_topics",
    "registered_types",
    "topic_to_entity_path",
]
