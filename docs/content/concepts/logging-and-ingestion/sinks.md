---
title: Sinks
order: 1000
description: The destinations logged data can be sent to
---

Sinks control where your Dalaran data goes. They are the output destinations for your logged data.

When you log data with Dalaran, that data needs to flow somewhere, whether that's to a live viewer, a file on disk, memory, or multiple destinations at once. Sinks provide this routing layer, giving you flexible control over how and where your recordings are stored and displayed.

## Available sink types

Dalaran provides several built-in sink types, each designed for specific use cases:

### GrpcSink

Streams data to a Dalaran Viewer over gRPC. This is the most common sink for live visualization.

snippet: concepts/grpc_sink

### FileSink

Writes data to `.dlr` files on disk.

snippet: concepts/file_sink

## Multiple sinks (Tee pattern)

One of the most powerful features of Dalaran's sink system is the ability to send data to multiple destinations simultaneously. This "tee" pattern lets you both visualize data live and save it to disk in a single run.

snippet: howto/set_sinks

This pattern is useful when:

- You want to monitor a long-running process while archiving the data
- You're debugging and want both live feedback and a recording to analyze later
- You need to stream to multiple viewers or save to multiple files

## See also

- [Recordings](recordings.md): Understand how recordings relate to sinks
- [Blueprints](../visualization/blueprints.md): Learn how to configure the viewer's layout
- API References:
  - [🐍 Python sinks API](https://ref.dalaran.dev/docs/python/stable/common/initialization_functions/)
  - [🦀 Rust RecordingStream](https://docs.rs/dalaran/latest/dalaran/struct.RecordingStream.html)
  - [🌊 C++ RecordingStream](https://ref.dalaran.dev/docs/cpp/stable/classdalaran_1_1RecordingStream.html)
