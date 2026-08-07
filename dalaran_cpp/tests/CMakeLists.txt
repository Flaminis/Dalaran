cmake_minimum_required(VERSION 3.16...3.27)

# Catch2:
Include(FetchContent)
FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.4.0
)

# To avoid that tests to not pass on Windows with BUILD_SHARED_LIBS=ON
# because the loader can't find Catch2.dll, we always compile Catch2 as static
if(WIN32 AND BUILD_SHARED_LIBS)
    set(BUILD_SHARED_LIBS_DALARAN_SDK ${BUILD_SHARED_LIBS})
    set(BUILD_SHARED_LIBS OFF)
endif()

FetchContent_MakeAvailable(Catch2)

if(WIN32 AND BUILD_SHARED_LIBS_DALARAN_SDK)
    set(BUILD_SHARED_LIBS ${BUILD_SHARED_LIBS_DALARAN_SDK})
endif()

file(GLOB_RECURSE dalaran_sdk_tests_SRC CONFIGURE_DEPENDS
    "*.hpp"
    "*.cpp"
)

# Add readme snippets to the tests to make sure they keep compiling.
list(APPEND dalaran_sdk_tests_SRC "../docs/readme_snippets.cpp")

add_executable(dalaran_sdk_tests ${dalaran_sdk_tests_SRC})

dalaran_strict_warning_settings(dalaran_sdk_tests)

# Include arrow explicitly again, otherwise the arrow headers won't be found.
target_link_libraries(dalaran_sdk_tests PRIVATE loguru::loguru Catch2::Catch2 dalaran_sdk dalaran_arrow_target)
