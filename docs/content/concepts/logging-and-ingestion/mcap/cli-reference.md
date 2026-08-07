---
title: CLI Reference for MCAP
order: 500
---

This reference guide covers all command-line options and workflows for working with MCAP files in Dalaran.

## Basic commands

### Direct viewing

Open MCAP files directly in the Dalaran Viewer:

```bash
# View a single MCAP file
dalaran data.mcap

# View multiple specific files
dalaran file1.mcap file2.mcap file3.mcap

# Use glob patterns to load all MCAP files in a directory
dalaran recordings/*.mcap

# Recursively load all MCAP files from a directory
dalaran mcap_data/
```

### File conversion

Convert MCAP files to Dalaran's native DLR format:

```bash
# Convert MCAP to DLR format for faster loading
dalaran mcap convert input.mcap -o output.dlr

# Convert with custom output location
dalaran mcap convert data.mcap -o /path/to/output.dlr
```

## Decoder selection

### Using specific decoders

Control which processing decoders are applied during conversion:

```bash
# Use only protobuf decoding and file statistics
dalaran mcap convert input.mcap -d protobuf -d stats -o output.dlr

# Use only ROS2 semantic interpretation for robotics data
dalaran mcap convert input.mcap -d ros2msg -o output.dlr

# Add robot geometry from ROS robot_description topics
dalaran mcap convert input.mcap -d ros2msg -d urdf -o output.dlr

# Combine multiple decoders for comprehensive data access
dalaran mcap convert input.mcap -d ros2msg -d raw -d recording_info -o output.dlr
```

### Available decoder options

Decoding:
- **`raw`**: Preserve original message bytes
- **`schema`**: Extract metadata and schema information
- **`stats`**: Compute file and channel statistics into DLR `__mcap_properties`
- **`metadata`**: Extract metadata records into DLR `__mcap_metadata`, if present
- **`attachments`**: Extract MCAP attachment records into static data under `__mcap_attachments`
- **`protobuf`**: Decode protobuf messages using into generic Arrow data without Dalaran visualization components
- **`recording_info`**: Extract recording session metadata into DLR `__mcap_properties`
- **`urdf`**: Use Dalaran's built-in URDF loader when a ROS 2 `/robot_description` topic is present

Semantic:
- **`foxglove`**: Semantic interpretation of Foxglove Protobuf messages
- **`ros2msg`**: Semantic interpretation of ROS2 messages

### Default behavior

When no `-d` flags are specified, all available decoders are used:

```bash
# These commands are equivalent (default uses all decoders):

dalaran mcap convert input.mcap -o output.dlr

dalaran mcap convert input.mcap \
    -d raw \
    -d attachments \
    -d schema \
    -d stats \
    -d metadata \
    -d protobuf \
    -d recording_info \
    -d urdf \
    -d ros2msg \
    -d foxglove \
    -o output.dlr
```
