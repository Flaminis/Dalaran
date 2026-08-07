"""Log a simple MCAP schema definition."""

import dalaran as dl

dl.init("dalaran_example_mcap_schema", spawn=True)

# Example ROS2 message definition for a simple Point message
point_schema = """float64 x
float64 y
float64 z"""

dl.log(
    "mcap/schemas/geometry_point",
    dl.McapSchema(
        id=42,
        name="geometry_msgs/msg/Point",
        encoding="ros2msg",
        data=point_schema.encode("utf-8"),
    ),
)
