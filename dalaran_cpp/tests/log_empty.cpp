#include <catch2/catch_test_macros.hpp>

#include <dalaran.hpp>

#include "error_check.hpp"

#define TEST_TAG "[log_empty][archetypes]"

// Regression test for #3840
SCENARIO("Log empty data", TEST_TAG) {
    dalaran::RecordingStream stream("empty archetype");

    SECTION("Using an existing archetype") {
        check_logged_error([&] {
            stream.log("empty", dalaran::Points3D(std::vector<dalaran::Position3D>{}));
        });
    }
    SECTION("Using an empty component batch") {
        check_logged_error([&] {
            stream.log(
                "empty",
                dalaran::ComponentBatch::empty<dalaran::Position3D>(
                    dalaran::Points3D::Descriptor_positions
                )
            );
        });
    }
}
