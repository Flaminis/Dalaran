<!--[metadata]
title = "MCAP"
description = "Load, convert, and post-process MCAP files in Dalaran, including conversion of older ROS 1/2 bags into MCAP and DLR."
tags = ["MCAP", "DLR", "ROS", "ROS 2", "Rosbag", "Tutorial"]
source = "https://github.com/rerun-io/mcap_example"
thumbnail = "https://static.rerun.io/mcap_example/7a3207652fa411979a96d5c5a25a43be29f1fdfb/480w.png"
thumbnail_dimensions = [480, 305]
-->

<video width="100%" autoplay loop muted controls>
    <source src="https://static.rerun.io/d69eb734367556854dcb167f8b8f8f9f6d3760e0_mcap_example.mp4" type="video/mp4" />
</video>

## Background

This example demonstrates how to visualize and work with [MCAP](https://mcap.dev/) files in Dalaran. From [mcap.dev](https://mcap.dev/):

> MCAP (pronounced "em-cap") is an open source container file format for multimodal log data. It supports multiple channels of timestamped pre-serialized data, and is ideal for use in pub/sub or robotics applications.

MCAP is the default bag format in ROS 2 and is rapidly gaining adoption. You can read more about [Dalaran's MCAP support here](https://dalaran.dev/docs/howto/mcap).

In this guide, you will learn:

1. How to **load MCAP files** directly into the Dalaran viewer.
2. How to **convert MCAP files** into native Dalaran data files (**DLR**).
3. How to **convert older ROS bags** (ROS 1 and ROS 2 SQLite3) into MCAP.
4. How to read and deserialize MCAP/DLR data in Python for programmatic processing and advanced visualization in Dalaran.

We will use a dataset from the [JKK Research Center](https://jkk-research.github.io/dataset/jkk_dataset_01/) containing LiDAR, images, GPS, and IMU data. The workflow involves converting the original ROS 1 bag → MCAP → DLR, and then using Python to log the DLR data with specific Dalaran components for optimal visualization.

## Follow the tutorial and run the code

This is an external example. Check the [mcap_example](https://github.com/rerun-io/mcap_example) repository for more information.
