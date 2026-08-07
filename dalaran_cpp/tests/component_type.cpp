#include <catch2/catch_test_macros.hpp>
#include <dalaran/component_type.hpp>

#include <dalaran/c/dalaran.h>

#include <arrow/api.h>

#define TEST_TAG "[component_type]"

SCENARIO("Component type registration" TEST_TAG) {
    GIVEN("A valid component type") {
        dalaran::ComponentType type("test", arrow::float64());

        WHEN("it is registered") {
            auto result = type.register_component();

            THEN("it succeeds") {
                REQUIRE(result.is_ok());
                CHECK(result.value != DL_COMPONENT_TYPE_HANDLE_INVALID);
            }
        }
    }

    GIVEN("A component type with an empty name") {
        dalaran::ComponentType type(std::string_view(), arrow::float64());

        WHEN("it is registered") {
            auto result = type.register_component();

            THEN("it fails with InvalidStringArgument") {
                CHECK(result.error.code == dalaran::ErrorCode::InvalidStringArgument);
            }
        }
    }
}
