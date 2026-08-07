#include "archetype_test.hpp"

#include <dalaran/archetypes/clear.hpp>

using namespace dalaran::archetypes;

#define TEST_TAG "[clear][archetypes]"

SCENARIO("clear archetype can be serialized" TEST_TAG) {
    GIVEN("Constructed from builder and manually") {
        auto from_builder = Clear(true);

        THEN("serialization succeeds") {
            CHECK(dalaran::AsComponents<Clear>().as_batches(from_builder).is_ok());
        }
    }
}
