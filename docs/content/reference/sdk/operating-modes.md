---
title: Operating Modes
order: 800
---

There are many different ways of sending data to the Dalaran Viewer depending on what you're trying to achieve and whether the Viewer is running in the same process as your code, in another process, or even as a separate web application.

In the [official examples](https://dalaran.dev/examples), these different modes of operation are exposed via a standardized set of flags that we'll cover below.
We will also demonstrate how you can achieve the same behavior in your own code.

Before reading this document, you might want to familiarize yourself with the [Dalaran application model](../../concepts/how-does-dalaran-work.md).

## Operating modes

The Dalaran SDK provides multiple modes of operation: `spawn`, `connect_grpc`, `serve_grpc`, `save`, and `stdout`.

All of them are optional: when none of these modes are active, the client will simply buffer the logged data in memory, waiting for one of these modes to be enabled so that it can flush it.

> [!WARNING]
> These modes will override each other and destroy any existing sinks; if you want to run multiple sinks concurrently, you'll need to use `set_sinks()`.

### `spawn`

This is the default behavior you get when running all of our C++/Python/Rust examples, and is generally the most convenient when you're experimenting.

#### C++
`RecordingStream::spawn` spawns a new Dalaran Viewer process using an executable available in your PATH, then streams all the data to it via gRPC. If an external Viewer was already running, `spawn` will connect to that one instead of spawning a new one.

#### Python
Call [`dl.spawn`](https://ref.dalaran.dev/docs/python/stable/common/initialization_functions/#dalaran.spawn) once at the start of your program to start a Dalaran Viewer in an external process and stream all the data to it via gRPC. If an external Viewer was already running, `spawn` will connect to that one instead of spawning a new one.

#### Rust
[`RecordingStream::spawn`](https://docs.rs/dalaran/latest/dalaran/struct.RecordingStream.html#method.spawn) spawns a new Dalaran Viewer process using an executable available in your PATH, then streams all the data to it via gRPC. If an external Viewer was already running, `spawn` will connect to that one instead of spawning a new one.


### `connect_grpc`

Connects to a remote Dalaran Viewer and streams all the data via gRPC.

You will need to start a stand-alone Viewer first by typing `dalaran` in your terminal.

#### C++
`RecordingStream::connect_grpc`

#### Python
[`dl.connect_grpc`](https://ref.dalaran.dev/docs/python/stable/common/initialization_functions/#dalaran.connect_grpc)

#### Rust
[`RecordingStream::connect_grpc`](https://docs.rs/dalaran/latest/dalaran/struct.RecordingStream.html#method.connect_grpc)


### `serve_grpc`
Calling `serve_grpc` will start a Dalaran gRPC server in your process, and stream logged data to it.
This gRPC server can then be connected to from the Dalaran Viewer, e.g. by running `dalaran --connect`.
The gRPC server acts as a proxy, buffering and forwarding log data to the Dalaran Viewer.

You can also connect to the gRPC server from a Dalaran Web Viewer.
To host a Dalaran Web Viewer, you can use the `serve_web_viewer` function.

snippet: howto/serve_web_viewer

#### C++
* [`RecordingStream::serve_grpc`](https://ref.dalaran.dev/docs/cpp/stable/classdalaran_1_1RecordingStream.html).
* TODO(#4638): `serve_web_viewer` is not available.

#### Python
* [`dl.serve_grpc`](https://ref.dalaran.dev/docs/python/stable/common/initialization_functions/#dalaran.serve_grpc)
* [`dl.serve_web_viewer`](https://ref.dalaran.dev/docs/python/stable/common/initialization_functions/#dalaran.serve_web_viewer)

#### Rust
* [`RecordingStream::serve_grpc`](https://docs.rs/dalaran/latest/dalaran/struct.RecordingStream.html#method.serve_grpc)
* [`RecordingStream::serve_web_viewer`](https://docs.rs/dalaran/latest/dalaran/struct.RecordingStream.html#method.serve_web_viewer)


### `save`

Streams all logging data into an `.dlr` file on disk, which can then be loaded into a stand-alone viewer.

To view the saved file, use `dalaran path/to/file.dlr`.

> [!NOTE]
> DLR files saved with Dalaran 0.23 or later can be opened with a newer Dalaran version.
> For more details and potential limitations, please refer to [our blog post](https://dalaran.dev/blog/release-0.23).

> [!WARNING]
> At the moment, we only guarantee compatibility across adjacent minor versions (e.g. Dalaran 0.24 can open RRDs from 0.23).

#### C++
Use `RecordingStream::save`.

#### Python
Use [`dl.save`](https://ref.dalaran.dev/docs/python/stable/common/initialization_functions/#dalaran.save).

#### Rust
Use [`RecordingStream::save`](https://docs.rs/dalaran/latest/dalaran/struct.RecordingStream.html#method.save).


### Standard Input/Output (`stdout`)

Streams all logging data to standard output, which can then be loaded by the Dalaran Viewer by streaming it from standard input.

#### C++

Use [`RecordingStream::stdout`](https://ref.dalaran.dev/docs/cpp/stable/classdalaran_1_1RecordingStream.html).

Check out our [dedicated example](https://github.com/rerun-io/rerun/tree/latest/examples/cpp/stdio/main.cpp).

#### Python

Use [`dl.stdout`](https://ref.dalaran.dev/docs/python/stable/common/initialization_functions/#dalaran.stdout).

Check out our [dedicated example](https://github.com/rerun-io/rerun/tree/latest/examples/python/stdio/stdio.py).

#### Rust

Use [`RecordingStream::stdout`](https://docs.rs/dalaran/latest/dalaran/struct.RecordingStream.html#method.stdout).

Check out our [dedicated example](https://github.com/rerun-io/rerun/tree/latest/examples/rust/stdio/src/main.rs).

### `set_sinks`

You can use this to log to multiple sinks concurrently, such as saving to disk while streaming to the viewer.

snippet: howto/set_sinks

#### Python

Use [`dl.set_sinks`](https://ref.dalaran.dev/docs/python/stable/common/initialization_functions/#dalaran.set_sinks)

#### Rust

Use [`RecordingStream::set_sinks`](https://docs.rs/dalaran/latest/dalaran/struct.RecordingStream.html#method.set_sinks)

#### C++

Use [`RecordingStream::set_sinks`](https://ref.dalaran.dev/docs/cpp/classdalaran_1_1RecordingStream.html#a92c9d3ecd3007d87b9c801fa33b140dc)


## Adding the standard flags to your programs

We provide helpers for both Python & Rust to effortlessly add and properly handle all of these flags in your programs.

- For Python, checkout the [`script_helpers`](https://ref.dalaran.dev/docs/python/stable/common/script_helpers/) module.
- For Rust, checkout our [`clap`]() [integration](https://docs.rs/dalaran/latest/dalaran/clap/index.html).

Have a look at the [official examples](https://dalaran.dev/examples) to see these helpers in action.
