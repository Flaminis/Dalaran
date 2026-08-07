cmake_minimum_required(VERSION 3.16...3.27)

# If you use the example outside of the Dalaran SDK you need to specify
# where the dalaran_c build is to be found by setting the `DALARAN_CPP_URL` variable.
# This can be done by passing `-DDALARAN_CPP_URL=<path to dalaran_sdk_cpp zip>` to cmake.
if(DEFINED DALARAN_REPOSITORY)
    add_executable(example_spawn_viewer main.cpp)
    dalaran_strict_warning_settings(example_spawn_viewer)
else()
    project(example_spawn_viewer LANGUAGES CXX)

    add_executable(example_spawn_viewer main.cpp)

    # Set the path to the dalaran_c build.
    set(DALARAN_CPP_URL "https://github.com/Flaminis/Dalaran/releases/latest/download/rerun_cpp_sdk.zip" CACHE STRING "URL to the dalaran_cpp zip.")

    # Download the dalaran_sdk
    include(FetchContent)
    FetchContent_Declare(dalaran_sdk URL ${DALARAN_CPP_URL})
    FetchContent_MakeAvailable(dalaran_sdk)
endif()

# Link against dalaran_sdk.
target_link_libraries(example_spawn_viewer PRIVATE dalaran_sdk)
