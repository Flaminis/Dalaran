# ------------------------------------------------------------------------------
# Dalaran C++ SDK
#
# For more information check README.md
# ------------------------------------------------------------------------------

cmake_minimum_required(VERSION 3.16...3.27)

project(dalaran_sdk LANGUAGES CXX)

message("Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION} (${CMAKE_CXX_COMPILER})")

set(DALARAN_CPP_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src" CACHE PATH "Dalaran include & source directory")

file(GLOB_RECURSE dalaran_sdk_SRC CONFIGURE_DEPENDS
    "${DALARAN_CPP_SOURCE_DIR}/*.hpp"
    "${DALARAN_CPP_SOURCE_DIR}/*.cpp"
)

add_library(dalaran_sdk ${dalaran_sdk_SRC} ${dalaran_sdk_PUBLIC_HEADER})

# Make sure the compiler can find include files for dalaran when other libraries or executables link to dalaran.
# Mark include directories as system includes to suppress warnings from them.
target_include_directories(dalaran_sdk PUBLIC
    $<BUILD_INTERFACE:${DALARAN_CPP_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include>
)

# Dalaran needs at least C++17.
target_compile_features(dalaran_sdk PUBLIC cxx_std_17)

# Do multithreaded compiling on MSVC.
if(MSVC)
    target_compile_options(dalaran_sdk PRIVATE "/MP")
endif()

# Set default warning settings if defined.
if(COMMAND dalaran_strict_warning_settings)
    message("Building Dalaran C++ SDK with strict compilation warnings.")
    dalaran_strict_warning_settings(dalaran_sdk)
endif()

# ------------------------------------------------------------------------------
# Setup dalaran_c dependency if it wasn't set up already.
if(NOT TARGET dalaran_c)
    add_library(dalaran_c STATIC IMPORTED GLOBAL)

    # Inside the repo build ourselves, otherwise default to a local `lib` folder.
    set(DALARAN_C_DEFAULT_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/lib/)

    if(APPLE)
        if("${CMAKE_SYSTEM_PROCESSOR}" STREQUAL "x86_64")
            message(WARNING "macOS x86 is officially unsupported by Dalaran.")
            set(DALARAN_C_LIB_DEFAULT ${DALARAN_C_DEFAULT_LIB_DIR}/libdalaran_c__macos_x64.a)
        elseif("${CMAKE_SYSTEM_PROCESSOR}" STREQUAL "arm64" OR "${CMAKE_SYSTEM_PROCESSOR}" STREQUAL "aarch64")
            set(DALARAN_C_LIB_DEFAULT ${DALARAN_C_DEFAULT_LIB_DIR}/libdalaran_c__macos_arm64.a)
        else()
            message(WARNING "Unknown architecture ${CMAKE_SYSTEM_PROCESSOR}, can't find dalaran_c library.")
        endif()
    elseif(UNIX) # if(LINUX) # CMake 3.25
        if("${CMAKE_SYSTEM_PROCESSOR}" STREQUAL "x86_64")
            set(DALARAN_C_LIB_DEFAULT ${DALARAN_C_DEFAULT_LIB_DIR}/libdalaran_c__linux_x64.a)
        elseif("${CMAKE_SYSTEM_PROCESSOR}" STREQUAL "arm64" OR "${CMAKE_SYSTEM_PROCESSOR}" STREQUAL "aarch64")
            set(DALARAN_C_LIB_DEFAULT ${DALARAN_C_DEFAULT_LIB_DIR}/libdalaran_c__linux_arm64.a)
        else()
            message(WARNING "Unknown architecture ${CMAKE_SYSTEM_PROCESSOR}, can't find dalaran_c library.")
        endif()
    elseif(WIN32)
        # TODO(andreas): Arm support.
        set(DALARAN_C_LIB_DEFAULT ${DALARAN_C_DEFAULT_LIB_DIR}/dalaran_c__win_x64.lib)
    else()
        message(WARNING "Unsupported platform ${DALARAN_C_LIB_DEFAULT}, can't find dalaran_c library.")
    endif()

    set(DALARAN_C_LIB ${DALARAN_C_LIB_DEFAULT} CACHE PATH "\
        Where to find the dalaran_c library.\n\
        If not specified, a local dalaran_c with the current system architecture will be used."
    )

    if("${DALARAN_C_LIB}" STREQUAL "")
        message(FATAL_ERROR "DALARAN_C_LIB is not set.")
    endif()

    set_target_properties(dalaran_c PROPERTIES IMPORTED_LOCATION ${DALARAN_C_LIB})
endif()

if(APPLE)
    target_link_libraries(dalaran_c INTERFACE "-framework CoreFoundation" "-framework IOKit" "-framework Security")
elseif(UNIX) # if(LINUX) # CMake 3.25
    target_link_libraries(dalaran_c INTERFACE "-lm -ldl -pthread")
elseif(WIN32)
    target_link_libraries(dalaran_c INTERFACE
        Crypt32
        Iphlpapi
        Ncrypt
        Netapi32
        ntdll
        Pdh
        PowrProf
        Psapi
        Secur32
        Userenv
        ws2_32
    )
endif()

# `dalaran_c` is a public dependency, meaning that all symbols from dalaran_c are available to consumers of `dalaran_sdk`.
# If we don't do that, then we can't have any inline functions using `dalaran_c` and users or `dalaran_sdk`
# can't call any `dalaran_c` methods directly.
target_link_libraries(dalaran_sdk PUBLIC dalaran_c)

# -----------------------------------------------------------------------------
# Arrow dependency.
# This makes the setup a lot easier on Windows where we otherwise need to put Arrow.dll either in path or copy it with the executable.
option(DALARAN_DOWNLOAD_AND_BUILD_ARROW "If enabled, arrow will be added as an external project and built with the minimal set required by the Dalaran C++ SDK" ON)

if (NOT DALARAN_DOWNLOAD_AND_BUILD_ARROW)
    find_package(Arrow REQUIRED)
endif()

if (ARROW_BUILD_SHARED)
    set(DALARAN_ARROW_LINK_SHARED_DEFAULT ON)
else()
    set(DALARAN_ARROW_LINK_SHARED_DEFAULT OFF)
endif()

option(DALARAN_ARROW_LINK_SHARED "Link to the Arrow shared library." ${DALARAN_ARROW_LINK_SHARED_DEFAULT})

if(DALARAN_DOWNLOAD_AND_BUILD_ARROW)
    include(download_and_build_arrow.cmake)
    download_and_build_arrow() # populates `dalaran_arrow_target`
else()
    if(DALARAN_ARROW_LINK_SHARED)
        add_library(dalaran_arrow_target ALIAS Arrow::arrow_shared)
    else()
        add_library(dalaran_arrow_target ALIAS Arrow::arrow_static)
    endif()
endif()

target_link_libraries(dalaran_sdk PRIVATE dalaran_arrow_target)

if(MSVC AND BUILD_SHARED_LIBS)
    # This code is required by to support BUILD_SHARED_LIBS=ON on Windows
    # Differently from Linux/macOS, by default Windows does not support
    # exporting all symbols of a shared library, and instead requires
    # annotating manually each class that needs to be exported
    # The WINDOWS_EXPORT_ALL_SYMBOLS PROPERTY (set in the next line)
    # simply the process of having shared library on Windows, by emulating
    # in CMake the behavior of Linux/macOS. However, it does not cover
    # static variables.
    set_property(TARGET dalaran_sdk PROPERTY WINDOWS_EXPORT_ALL_SYMBOLS ON)

    # For exporting static variables in shared libraries in Windows, it
    # is not possible to just use WINDOWS_EXPORT_ALL_SYMBOLS, we need instead
    # to manually annotate with the appropriate storage-class attributes
    # all static variables. The easiest way to do so is use GenerateExportHeader
    # module to generate a dalaran_sdk_export.hpp header file that define the DALARAN_SDK_EXPORT
    # macro, and add that macro to all static variables. The DALARAN_SDK_EXPORT is defined
    # in src/dalaran/dalaran_sdk_export.hpp . The definition of the macro changes depending
    # of whether the library is compiled as static or shared, so for shared builds we
    # set the DALARAN_SDK_COMPILED_AS_SHARED_LIBRARY to let the header know if the build
    # is a shared library one
    target_compile_definitions(dalaran_sdk PUBLIC DALARAN_SDK_COMPILED_AS_SHARED_LIBRARY)
endif()

# -----------------------------------------------------------------------------
# Installation.
set(DALARAN_SDK_INSTALL_CMAKE_DIR "lib/cmake/dalaran_sdk")

# Actual install setup.
install(TARGETS dalaran_sdk
    EXPORT dalaran_sdkTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
    INCLUDES DESTINATION include
)

# Some public headers are shared by both the C++ and C sdk, so we install
# them with the C++ headers also if DALARAN_INSTALL_DALARAN_C is OFF
set(DALARAN_PATTERN_HEADER_SHARED_BETWEEN_CXX_AND_C "sdk_info.h")

# Add all C++ headers to the install.
install(DIRECTORY "${DALARAN_CPP_SOURCE_DIR}/" TYPE INCLUDE FILES_MATCHING PATTERN "*.hpp" PATTERN ${DALARAN_PATTERN_HEADER_SHARED_BETWEEN_CXX_AND_C})

option(DALARAN_INSTALL_DALARAN_C "Install dalaran_c file." ON)

# if dalaran_sdk is a static library it is compulsory to install dalaran_c
get_target_property(dalaran_sdk_TYPE dalaran_sdk TYPE)

if(dalaran_sdk_TYPE STREQUAL "STATIC_LIBRARY" AND NOT DALARAN_INSTALL_DALARAN_C)
    message(FATAL_ERROR "It is not possible to disable DALARAN_INSTALL_DALARAN_C option if dalaran_sdk is compiled as static library.")
endif()

if(DALARAN_INSTALL_DALARAN_C)
    # CMake doesn't allow installing imported targets which is why we need to add this as a file.
    get_target_property(DALARAN_C_LIB_LOCATION dalaran_c IMPORTED_LOCATION)
    install(DIRECTORY "${DALARAN_CPP_SOURCE_DIR}/" TYPE INCLUDE FILES_MATCHING PATTERN "*.h" PATTERN ${DALARAN_PATTERN_HEADER_SHARED_BETWEEN_CXX_AND_C} EXCLUDE)
    install(FILES ${DALARAN_C_LIB_LOCATION} DESTINATION lib)
endif()

# Similarly, we bundle the arrow library that was used during the build.
# For the moment we only support this when building with the downloaded, static libarrow.
# Otherwise, a system install of arrow has to be used.
get_target_property(DALARAN_ARROW_LIB_LOCATION dalaran_arrow_target LOCATION)

if(DALARAN_DOWNLOAD_AND_BUILD_ARROW AND NOT DALARAN_ARROW_LINK_SHARED)
    get_target_property(DALARAN_ARROW_LIBRARY_FILE dalaran_arrow_target LOCATION)
    get_target_property(DALARAN_ARROW_BUNDLED_DEPENDENCIES_FILE arrow_targetBundledDeps LOCATION)
    install(FILES
        ${DALARAN_ARROW_LIBRARY_FILE}
        ${DALARAN_ARROW_BUNDLED_DEPENDENCIES_FILE}
        DESTINATION lib
    )
endif()

# Export the target to a script.
install(EXPORT dalaran_sdkTargets
    FILE dalaran_sdkTargets.cmake
    DESTINATION ${DALARAN_SDK_INSTALL_CMAKE_DIR}
)

include(CMakePackageConfigHelpers)

# Extract the version from dalaran.h.
# Intentionally only grab major.minor.patch, not the full version, since version file can't handle it otherwise.
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/src/dalaran/c/sdk_info.h" DALARAN_H_CONTENTS)
string(REGEX MATCH "\n#define DALARAN_SDK_HEADER_VERSION \"([0-9]+.[0-9]+.[0-9]+)" _ ${DALARAN_H_CONTENTS})
set(DALARAN_INSTALL_VERSION ${CMAKE_MATCH_1})
message(STATUS "Dalaran SDK install version: ${DALARAN_INSTALL_VERSION}")

# Package config file, so find_package(dalaran_sdk) produces a target.
configure_package_config_file(${CMAKE_CURRENT_SOURCE_DIR}/Config.cmake.in
    "${CMAKE_CURRENT_BINARY_DIR}/dalaran_sdkConfig.cmake" # file needs to follow convention of find_package.
    INSTALL_DESTINATION ${DALARAN_SDK_INSTALL_CMAKE_DIR}
    NO_SET_AND_CHECK_MACRO
    NO_CHECK_REQUIRED_COMPONENTS_MACRO
)

# Version file for find_package.
write_basic_package_version_file(
    ${CMAKE_CURRENT_BINARY_DIR}/dalaran_sdkConfigVersion.cmake
    VERSION ${DALARAN_INSTALL_VERSION}
    COMPATIBILITY ExactVersion
)

# Add the find_package dependent files.
install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/dalaran_sdkConfig.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/dalaran_sdkConfigVersion.cmake"
    DESTINATION ${DALARAN_SDK_INSTALL_CMAKE_DIR}
)

# -----------------------------------------------------------------------------
# Add tests if they exist (they are not part of the distribution zip).
# Has direct dependency to arrow, so needs to happen last.
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/tests)
    add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/tests)
endif()
