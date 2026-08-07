\mainpage
\tableofcontents

# Dalaran C++ SDK

The Dalaran C++ SDK allows logging data to Dalaran directly from C++.

## Getting started

Read the [getting started guide](https://www.dalaran.dev/docs/getting-started/data-in/cpp) on how to use the Dalaran C++ SDK.

### Logging

After you've [installed the viewer](https://www.dalaran.dev/docs/overview/installing-dalaran/viewer) and added the SDK to your project, you can jump right in and try logging some data.

You first create a `dalaran::RecordingStream` stream and spawn a viewer. You then use it to log some archetypes to a given entity path using `dalaran::RecordingStream::log`:

\snippet{trimleft} readme_snippets.cpp Logging

### Streaming to disk

Streaming data to a file on disk using the .dlr format:

\snippet{trimleft} readme_snippets.cpp Streaming

### Connecting

Instead of spawning a new viewer, you can also try to connect to an already open one.

\snippet{trimleft} readme_snippets.cpp Connecting

### Buffering

As long as you haven't called `dalaran::RecordingStream::save`/`dalaran::RecordingStream::connect_grpc`/`dalaran::RecordingStream::spawn`
any data will be kept in memory until you call one of these.

\snippet{trimleft} readme_snippets.cpp Buffering


## Examples

As general entry point for Dalaran examples check the [examples page](https://www.dalaran.dev/examples) on our website.
All C++ examples can be found [directly in the Dalaran repository](https://github.com/Flaminis/Dalaran/tree/latest/examples/cpp).
Additionally, each [archetype's documentation](https://www.dalaran.dev/docs/reference/types) comes with at least one small self-contained code example.


## Building blocks

The most important type in the SDK is the `dalaran::RecordingStream`.
It allows you to connect to the Dalaran Viewer and send data.

The built-in types are distributed to the respective namespaces:
* `dalaran::archetypes`
* `dalaran::components`
* `dalaran::datatypes`

If you include `dalaran.hpp`, all archetypes and most component types become part of the `dalaran` namespace.

Check the [general doc page on types](https://www.dalaran.dev/docs/reference/types) to learn more.

## Build & distribution

### Overview

From a build system perspective, the SDK consists of three dependencies:

* [C++ SDK source](https://github.com/Flaminis/Dalaran/tree/latest/rerun_cpp/src/)
  * This includes **both** source and header files!
  * To avoid compatibility issues across different platforms, compiler versions and C++ standard library versions
we recommend to build the C++ SDK directly from source.
Note that this also what happens when you follow the CMake setup in the [quickstart guide](https://www.dalaran.dev/docs/getting-started/data-in/cpp).
* [dalaran_c](https://github.com/Flaminis/Dalaran/tree/latest/crates/top/rerun_c/) static libraries
  * Dalaran C is a minimal C SDK and forms the bridge to the shared Rust codebase
  * Due to the rigidity of the C ABI and lack of complex standard library types in the interface,
    compatibility issues between compilers are less of a concern
    which is why we offer pre-built libraries with every release for all major platforms
* [Apache Arrow C++ library](https://arrow.apache.org/docs/cpp/index.html)
  * The SDK uses this library to perform all serialization before handing data over to dalaran_c
  * See [Install Arrow C++](arrow_cpp_install.md) for how to install this library


### SDK bundle (dalaran_cpp_sdk.zip)

For convenience, Dalaran provides a C++ SDK bundle with every release.
You can find the latest release artifacts [here](https://github.com/Flaminis/Dalaran/releases/latest).

This is a simple zip archive containing the SDK from the [repository](https://github.com/Flaminis/Dalaran/tree/latest/rerun_cpp)
(excluding the `tests` folder) and a `lib` folder with prebuilt dalaran_c libraries for all major desktop platforms.
The dalaran_c libraries follow a simple name schema that the CMake script can pick up.


### Building with CMake

See [CMake Setup in Detail](cmake_setup_in_detail.md) for deeper dive on
how to use the SDK's `CMakeLists.txt` and an overview over all CMake configuration options.

### Without CMake

We don't have first class support for other build systems yet,
but it should be possible to setup Dalaran C++ without CMake fairly easily:

You have to add all files from the [src/](https://github.com/Flaminis/Dalaran/tree/latest/rerun_cpp/src/) folder
either directly to your project or a library.
In addition, you need to link the `dalaran_c` libraries and the [Arrow C++ library](https://arrow.apache.org/docs/cpp/index.html).
For more information on how to install Arrow, see [Install Arrow C++](arrow_cpp_install.md).

Make sure to compile with C++17 or newer.

#### Bazel

There's a user provided minimal Bazel example here: https://github.com/kyle-figure/bazel-minimal-dalaran/

### Install with conda package

If you are using a package manager that supports conda packages such as `conda` or `pixi` to manage your C++ dependencies,
the Dalaran C++ SDK is available from conda-forge channel in the [`libdalaran-sdk` package]().
After you installed the `libdalaran-sdk` package. The Dalaran Viewer is instead provided by the
`dalaran-sdk` package, and you can install both with:

```bash
conda install -c conda-forge libdalaran-sdk dalaran-sdk
```

or

```bash
pixi add libdalaran-sdk dalaran-sdk
```

Once the package is available, you can find and consume it in your CMake project
as you consume any other installed C++ library that provides a CMake config file:

```cmake
find_package(dalaran_sdk REQUIRED)

# …

target_link_libraries(<yourtarget> PRIVATE dalaran_sdk)
```

### Install with vcpkg

The Dalaran C++ SDK is also available as the community-maintained [`dalaran-sdk` vcpkg port](https://vcpkg.io/en/package/dalaran-sdk).
You can install it with:

```bash
vcpkg install dalaran-sdk
```

Once installed, consume it from CMake like any other vcpkg-provided package:

```cmake
find_package(dalaran_sdk CONFIG REQUIRED)

target_link_libraries(<yourtarget> PRIVATE dalaran_sdk)
```

## Development in the Dalaran repository

Refer to the [build instruction](https://github.com/Flaminis/Dalaran/tree/latest/BUILD.md) at the repo root.

Keep in mind that all archetypes/components/datatypes are mostly generated by the [Dalaran types builder](https://github.com/Flaminis/Dalaran/tree/latest/crates/build/dl_types_builder).
Use `pixi run codegen` to run code generation. Generally, all generated code files are part of the repository,
so you only have to do that if you change the data definition or make changes to `_ext.cpp` files which
extend generated types.

## Tested compilers

The Dalaran C++ SDK requires a C++17 compliant compiler.

As of writing we tested the SDK against:
* Apple Clang 14, 15
* GCC 9, 10, 12
* Visual Studio 2022
