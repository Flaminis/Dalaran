# Builds dalaran_c from source.

# Determine build configuration (Debug or Release)
string(TOLOWER "${CMAKE_BUILD_TYPE}" CMAKE_BUILD_TYPE_LOWER)

if(CMAKE_BUILD_TYPE_LOWER STREQUAL "debug")
    set(CARGO_BUILD_FLAG "")
    set(RUST_BUILD_TYPE "debug")
    message("Building DEBUG BUILD of Dalaran C++ SDK")
else()
    message("Building RELEASE BUILD of Dalaran C++ SDK")
    set(CARGO_BUILD_FLAG "--release")
    set(RUST_BUILD_TYPE "release")
endif()

# Determine Rust's libdalaran path.
if(DEFINED ENV{CARGO_TARGET_DIR})
    set(CARGO_TARGET_DIR $ENV{CARGO_TARGET_DIR})
else()
    set(CARGO_TARGET_DIR "target")
endif()

if(NOT IS_ABSOLUTE ${CARGO_TARGET_DIR})
    set(CARGO_TARGET_DIR ${PROJECT_SOURCE_DIR}/${CARGO_TARGET_DIR})
endif()

if(APPLE)
    set(DALARAN_C_BUILD_ARTIFACT ${CARGO_TARGET_DIR}/$ENV{CARGO_BUILD_TARGET}/${RUST_BUILD_TYPE}/libdalaran_c.a)
elseif(UNIX) # if(LINUX) # CMake 3.25
    set(DALARAN_C_BUILD_ARTIFACT ${CARGO_TARGET_DIR}/$ENV{CARGO_BUILD_TARGET}/${RUST_BUILD_TYPE}/libdalaran_c.a)
elseif(WIN32)
    set(DALARAN_C_BUILD_ARTIFACT ${CARGO_TARGET_DIR}/$ENV{CARGO_BUILD_TARGET}/${RUST_BUILD_TYPE}/dalaran_c.lib)
else()
    message(FATAL_ERROR "Unsupported platform.")
endif()

# Setup dalaran_c library
add_library(dalaran_c STATIC IMPORTED GLOBAL)
set_target_properties(dalaran_c PROPERTIES IMPORTED_LOCATION ${DALARAN_C_BUILD_ARTIFACT})

# Just depend on all rust and toml files, it's hard to know which files exactly are relevant.
file(GLOB_RECURSE DALARAN_C_SOURCES LIST_DIRECTORIES FALSE "${PROJECT_SOURCE_DIR}/crates/*.rs" "${PROJECT_SOURCE_DIR}/crates/*.toml")
add_custom_command(
    OUTPUT ${DALARAN_C_BUILD_ARTIFACT}
    DEPENDS ${DALARAN_C_SOURCES}
    COMMAND cargo build ${CARGO_BUILD_FLAG} -p dalaran_c
    COMMENT "Building dalaran_c from source"
    WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
)

# In CMake you can't depend on an output file directly. We have to wrap this in a target that dalaran_c then depends on.
add_custom_target(dalaran_c_build DEPENDS "${DALARAN_C_BUILD_ARTIFACT}")
add_dependencies(dalaran_c dalaran_c_build)
