"""Log a simple MCAP channel definition."""

import dalaran as dl

dl.init("dalaran_example_mcap_channel", spawn=True)

dl.log(
    "mcap/channels/camera",
    dl.McapChannel(
        id=1,
        topic="/camera/image",
        message_encoding="cdr",
        metadata={"frame_id": "camera_link", "encoding": "bgr8"},
    ),
)
