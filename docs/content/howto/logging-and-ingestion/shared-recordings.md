---
title: Share recordings across multiple processes
order: 400
description: Log to a single recording from multiple processes
---

A common need is to log data from multiple processes and then visualize all of that data as part of a single shared recording.

Dalaran has the notion of a [Recording ID](../../concepts/logging-and-ingestion/recordings.md) for that: any recorded datasets that share the same Recording ID will be visualized as one shared dataset.

The data can be logged from any number of processes, whether they run on the same machine or not, or implemented in different programming languages.
All that matter is that they share the same Recording ID.

By default, Dalaran generates a random Recording ID everytime you start a new logging session, but you can override that behavior, e.g.:

snippet: tutorials/custom-recording-id

It's up to you to decide where each recording ends up:
- all processes could stream their share of the data in real-time to a Dalaran Viewer,
- or maybe they all write to their own file on disk that are later loaded in a viewer,
- or some other combination of the above.

Here's a simple example of such a workflow:
```python
# Process 1 logs some spheres to a recording file.
./app1.py  # dl.init(recording_id='my_shared_recording', dl.save('/tmp/recording1.dlr')

# Process 2 logs some cubes to another recording file.
./app2.py  # dl.init(recording_id='my_shared_recording', dl.save('/tmp/recording2.dlr')

# Visualize a 3D scene with both spheres and cubes.
dalaran /tmp/recording*.dlr  # they share the same Recording ID!
```

For more information, check out our dedicated examples:
* [🐍 Python](https://github.com/Flaminis/Dalaran/blob/latest/examples/python/shared_recording/shared_recording.py)
* [🦀 Rust](https://github.com/Flaminis/Dalaran/blob/latest/examples/rust/shared_recording/src/main.rs)
* [🌊 C++](https://github.com/Flaminis/Dalaran/blob/latest/examples/cpp/shared_recording/main.cpp)


### Merging recordings with the Dalaran CLI

It is possible to merge multiple recording files into a single one using the [Dalaran CLI](../../reference/cli.md#dalaran-dlr-merge), e.g. `dalaran dlr merge -o merged_recordings.dlr my_first_recording.dlr my_second_recording.dlr`.

The Dalaran CLI offers several options to manipulate recordings in different ways, check out [the CLI reference](../../reference/cli.md) for more information.
