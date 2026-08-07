"""Log simple MCAP recording statistics."""

import dalaran as dl

dl.init("dalaran_example_mcap_statistics", spawn=True)

dl.log(
    "mcap/statistics/recording_overview",
    dl.McapStatistics(
        message_count=12500,
        schema_count=3,
        channel_count=5,
        attachment_count=2,
        metadata_count=8,
        chunk_count=25,
        # 2024-04-01 00:00:00 UTC in nanoseconds
        message_start_time=1743465600000000000,
        # 2024-04-01 00:10:00 UTC in nanoseconds (10 minute recording)
        message_end_time=1743466200000000000,
    ),
)
