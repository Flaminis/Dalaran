#include "archetype_test.hpp"

#include <dalaran/archetypes/view_coordinates.hpp>
#include <dalaran/components/view_coordinates.hpp>

using namespace dalaran::archetypes;

#define TEST_TAG "[view_coordinates][archetypes]"

SCENARIO(
    "ViewCoordinates archetype can be serialized with the same result whether from builder, static "
    "const, or manually.",
    TEST_TAG
) {
    GIVEN("Constructed from builder and manually") {
        auto from_builder = ViewCoordinates(
            dalaran::datatypes::ViewDir::Right,
            dalaran::datatypes::ViewDir::Down,
            dalaran::datatypes::ViewDir::Forward
        );

        ViewCoordinates from_manual;
        from_manual.xyz = dalaran::ComponentBatch::from_loggable<dalaran::components::ViewCoordinates>(
                              {
                                  dalaran::datatypes::ViewDir::Right,
                                  dalaran::datatypes::ViewDir::Down,
                                  dalaran::datatypes::ViewDir::Forward,
                              },
                              ViewCoordinates::Descriptor_xyz
        )
                              .value_or_throw();

        test_compare_archetype_serialization(from_manual, from_builder);
    }

    GIVEN("Constructed from builder and static") {
        auto from_builder = ViewCoordinates(
            dalaran::datatypes::ViewDir::Right,
            dalaran::datatypes::ViewDir::Down,
            dalaran::datatypes::ViewDir::Forward
        );

        test_compare_archetype_serialization(ViewCoordinates::RDF, from_builder);
    }
}
