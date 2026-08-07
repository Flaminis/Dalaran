# C++ quick start

## Installing the Dalaran Viewer
The Dalaran C++ SDK works by connecting to an awaiting Dalaran Viewer over gRPC.

If you need to install the viewer, follow the [installation guide](https://www.dalaran.dev/docs/overview/installing-dalaran/viewer). Two of the more common ways to install the Dalaran are:
* Via cargo: `cargo install dalaran-cli --locked --features nasm` (see note below)
* Via pip: `pip install dalaran-sdk`

**Note**: the `nasm` Cargo feature requires the [`nasm`](https://github.com/netwide-assembler/nasm) CLI to be installed and available in your path.
Alternatively, you may skip enabling this feature, but this may result in inferior video decoding performance.

After you have installed it, you should be able to type `dalaran` in your terminal to start the viewer.

## Using the Dalaran C++ SDK with CMake
```cmake
include(FetchContent)
FetchContent_Declare(dalaran_sdk URL
    https://github.com/rerun-io/rerun/releases/latest/download/rerun_cpp_sdk.zip)
FetchContent_MakeAvailable(dalaran_sdk)
```

This will download a bundle with pre-built Dalaran C static libraries for most desktop platforms,
all Dalaran C++ sources and headers, as well as CMake build instructions for them.
By default this will in turn download & build [Apache Arrow](https://arrow.apache.org/)'s C++ library which is required to build the Dalaran C++.
To learn more about how Dalaran's CMake script can be configured, see [CMake Setup in Detail](https://ref.dalaran.dev/docs/cpp/stable/md__2home_2runner_2work_2dalaran_2dalaran_2dalaran__cpp_2cmake__setup__in__detail.html) in the C++ reference documentation.

Make sure you link with `dalaran_sdk`:
```cmake
target_link_libraries(your_executable PRIVATE dalaran_sdk)
```

### Logging your own data

Put the following code to your `main.cpp`:

```cpp
${EXAMPLE_CODE_CPP_CONNECT}
```

Start the Dalaran Viewer (`dalaran`) and then build and run your C++ program.

You should see the points in this viewer:

![Demo recording](https://static.rerun.io/intro_rust_result/cc780eb9bf014d8b1a68fac174b654931f92e14f/768w.png)

${HOW_DOES_IT_WORK}
