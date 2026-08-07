---
title: Use multiple native viewers
order: 100
description: Run several Viewer windows on different gRPC ports
---

You can run multiple Native Viewer windows simultaneously, each displaying different data or views of the same data.

## How it works

Every Native Viewer binds to a gRPC port on startup. By default, this is port `9876`. When you run `dalaran`, it checks if a viewer is already listening on that port:

- **If yes**: it connects to the existing viewer (or sends data to it)
- **If no**: it starts a new viewer on that port

To open multiple viewer windows, use different ports with the `--port` flag.

## Examples

```sh
# Start a viewer on the default port (9876)
$ dalaran &

# This does nothing — a viewer is already running on :9876
$ dalaran &

# Start a second viewer on port 6789
$ dalaran --port 6789 &

# Log an image to the first viewer (port 9876)
$ dalaran image.jpg

# Log an image to the second viewer (port 6789)
$ dalaran --port 6789 image.jpg
```

## From the SDK

When using `connect_grpc()` from the SDK, specify the port to target a specific viewer:

```python
import dalaran as dl

# Connect to viewer on default port
dl.init("dalaran_example_demo")
dl.connect_grpc()

# Or connect to a specific port
dl.connect_grpc("dalaran+http://127.0.0.1:6789")
```

## Tips

- Use `spawn()` to automatically start a new viewer if needed — it will reuse an existing viewer on the default port if one is running
- Each viewer maintains its own Chunk Store, so data sent to different viewers is independent
- The Web Viewer doesn't use gRPC ports the same way — it connects via WebSocket when served locally
