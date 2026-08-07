cmake_minimum_required(VERSION 3.16...3.27)

# If you use the example outside of the Dalaran SDK you need to specify
# where the dalaran_c build is to be found by setting the `DALARAN_CPP_URL` variable.
# This can be done by passing `-DDALARAN_CPP_URL=<path to dalaran_sdk_cpp zip>` to cmake.
if(DEFINED DALARAN_REPOSITORY)
    add_executable(example_log_file main.cpp)
    dalaran_strict_warning_settings(example_log_file)
else()
    project(example_log_file LANGUAGES CXX)

    add_executable(example_log_file main.cpp)

    # Set the path to the dalaran_c build.
    set(DALARAN_CPP_URL "https://github.com/Flaminis/Dalaran/releases/latest/download/dalaran_cpp_sdk.zip" CACHE STRING "URL to the dalaran_cpp zip.")
    option(DALARAN_FIND_PACKAGE "Whether to use find_package to find a preinstalled dalaran package (instead of using FetchContent)." OFF)

    if(DALARAN_FIND_PACKAGE)
        find_package(dalaran_sdk REQUIRED)
    else()
        # Download the dalaran_sdk
        include(FetchContent)
        FetchContent_Declare(dalaran_sdk URL ${DALARAN_CPP_URL})
        FetchContent_MakeAvailable(dalaran_sdk)
    endif()
endif()

# Link against dalaran_sdk.
target_link_libraries(example_log_file PRIVATE dalaran_sdk)
