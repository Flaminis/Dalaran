#include <catch2/catch_test_macros.hpp>

#include <dalaran.hpp>

#define TEST_TAG "[set_enabled]"

SCENARIO("Dalaran default_enabled can be configured", TEST_TAG) {
    GIVEN("The initial state") {
        THEN("The default value of default_enabled is true") {
            CHECK(dalaran::is_default_enabled());
        }
    }

    GIVEN("Logging has been disabled") {
        dalaran::set_default_enabled(false);

        THEN("default_enabled returns false") {
            CHECK_FALSE(dalaran::is_default_enabled());
        }
    }

    // NOTE: This needs to go last or else we end up globally disabling
    // default recordings, which breaks other tests.
    GIVEN("Logging has been enabled") {
        dalaran::set_default_enabled(true);

        THEN("default_enabled returns true") {
            CHECK(dalaran::is_default_enabled());
        }
    }
}
