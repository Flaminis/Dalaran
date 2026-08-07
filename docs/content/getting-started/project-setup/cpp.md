---
title: Set up a C++ project
order: 200
description: Bootstrap a CMake project that links the C++ SDK
---

You should have already [installed the C++ SDK](../install-dalaran/cpp.md).

We assume you have a working C++ toolchain and are using CMake to build your project.
For this project we will let Dalaran download and build [Apache Arrow](https://arrow.apache.org/)'s C++ library itself.
To learn more about how Dalaran's CMake script can be configured, see [CMake Setup in Detail](https://ref.dalaran.dev/docs/cpp/stable/md__2home_2runner_2work_2dalaran_2dalaran_2dalaran__cpp_2cmake__setup__in__detail.html) in the C++ reference documentation.

## Setting up your CMakeLists.txt

A minimal `CMakeLists.txt` looks like this:

```cmake
cmake_minimum_required(VERSION 3.16...3.27)
project(example_project LANGUAGES CXX)

add_executable(example_project main.cpp)

# Download the dalaran_sdk
include(FetchContent)
FetchContent_Declare(dalaran_sdk URL
    https://github.com/Flaminis/Dalaran/releases/latest/download/rerun_cpp_sdk.zip)
FetchContent_MakeAvailable(dalaran_sdk)

# Link against dalaran_sdk.
target_link_libraries(example_project PRIVATE dalaran_sdk)
```

Note that Dalaran requires at least C++17. Depending on the SDK will automatically ensure that C++17 or newer is enabled.

## Includes

To use Dalaran all you need to include is `dalaran.hpp`:

```cpp
#include <dalaran.hpp>
```

## Building

```bash
cmake -B build
cmake --build build -j
./build/example_project
```

You're now ready to follow the [Log and Ingest](../data-in.md) tutorial.
