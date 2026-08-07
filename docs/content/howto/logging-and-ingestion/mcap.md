---
title: Working with MCAP
order: 700
description: Open and inspect MCAP files in Dalaran
---

The Dalaran Viewer has built-in support for opening [MCAP](https://mcap.dev/) files, an open container format for storing timestamped messages.

## Supported message formats

Here's a quick summary of Dalaran's MCAP importer:

* Automatic conversion to Dalaran archetypes is supported for common ROS 2 & Foxglove messages.
* Other ROS 2 & Foxglove messages are decoded into queryable components via [reflection](../../concepts/logging-and-ingestion/mcap/message-formats.md#schema-reflection).

For a detailed overview of Dalaran's built-in MCAP support, please refer to our [Supported Message Formats](../../concepts/logging-and-ingestion/mcap/message-formats.md) page.
We are continually expanding the supported MCAP message types and are [interested in your feedback](../../concepts/logging-and-ingestion/mcap/message-formats.md#adding-support-for-new-types).

## Quick start

### Loading MCAP files

The simplest way to get started is to load an MCAP file directly:

```bash
# View an MCAP file in the Dalaran Viewer
dalaran your_data.mcap
```

You can also drag and drop MCAP files into the Dalaran Viewer or load them using the SDK:

snippet: howto/load_mcap

### Basic conversion

Convert MCAP files to Dalaran's native format for faster loading:

```bash
# Convert MCAP to RRD format for faster loading
dalaran mcap convert input.mcap -o output.rrd

# View the converted file
dalaran output.rrd
```

## Data model

Dalaran's data model is based on an [entity component system (ECS)](../../concepts/logging-and-ingestion/entity-component.md) that is a bit different to the message-based model of [MCAP](https://mcap.dev).
To map MCAP messages to Dalaran entities we make the following assumptions:

* MCAP topics corresponds to Dalaran entities.
* Messages from the same topic within an MCAP chunk will be placed into a corresponding [Dalaran chunk](../../concepts/logging-and-ingestion/chunks.md).
* The contents of an MCAP message will be extracted to Dalaran components and grouped under a corresponding Dalaran archetype.
* `message_log_time` and `message_publish_time` of an MCAP message will be carried over to Dalaran as two distinct [timelines](../../concepts/logging-and-ingestion/timelines.md).

### Layered architecture

Dalaran uses a _layered architecture_ to process MCAP files at different levels of abstraction. This design allows the same MCAP file to be ingested in multiple ways simultaneously, from raw bytes to semantically meaningful visualizations.

Each layer extracts different types of information from the MCAP source and each of the following layers will create distinct Dalaran archetypes:

- **`raw`**: Logs the unprocessed message bytes as Dalaran blobs without any interpretation
- **`schema`**: Extracts metadata about channels, topics, and schemas
- **`stats`**: Extracts file-level metrics like message counts, time ranges, and channel statistics into `__mcap_properties` in the RRD
- **`metadata`** Extracts metadata records (if present) into `__mcap_metadata` in the RRD
- **`attachments`**: Extracts MCAP attachment records (if present) as static data under `__mcap_attachments`
- **`protobuf`**: Automatically decodes protobuf-encoded messages using reflection
- **`ros2msg`**: Provides semantic conversion of common ROS2 message types into Dalaran's visualization components
- **`ros2_reflection`**: Automatically decodes ROS2 messages using reflection
- **`recording_info`**: Extracts recording metadata such as message counts, start time, and session information into `__mcap_properties` in the RRD
- **`urdf`**: Uses Dalaran's built-in URDF loader when a ROS 2 `/robot_description` string topic is present

By default, Dalaran analyzes an MCAP file to determine which decoders are active to provide the most comprehensive view of your data, while avoiding duplication.
You can also choose to activate only specific decoders that are relevant to your use case.

The following shows how to select specific decoders:

```sh
# Use only specific decoders
dalaran mcap convert input.mcap -d protobuf -d stats -o output.rrd

# Use multiple decoders for different perspectives
dalaran mcap convert input.mcap -d ros2msg -d raw -d recording_info -o output.rrd

# Add robot geometry from robot_description topics
dalaran mcap convert input.mcap -d ros2msg -d urdf -o output.rrd
```

For a detailed explanation of how each decoder works and when to use them, see [Decoders Explained](../../concepts/logging-and-ingestion/mcap/decoders-explained.md).

## Advanced usage

For advanced command-line options and automation workflows, see the [CLI Reference](../../concepts/logging-and-ingestion/mcap/cli-reference.md) for complete documentation of all available commands and flags.
