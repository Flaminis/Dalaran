"""Log a simple MCAP message with binary data."""

import dalaran as dl

dl.init("dalaran_example_mcap_message", spawn=True)

# Example binary message data (could be from a ROS message, protobuf, etc.)
# This represents a simple sensor reading encoded as bytes
sensor_data = (
    b"sensor_reading: temperature=23.5, humidity=65.2, timestamp=1743465600"
)

dl.log(
    "mcap/messages/sensor_reading",
    dl.McapMessage(
        data=sensor_data,
    ),
)
