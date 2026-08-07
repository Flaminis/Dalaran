#include "archetype_test.hpp"

#include <dalaran/archetypes/points2d.hpp>

using namespace dalaran::archetypes;

#define TEST_TAG "[points2d][archetypes]"

SCENARIO(
    "Points2D archetype can be serialized with the same result for manually built instances and "
    "the builder pattern",
    TEST_TAG
) {
    GIVEN("Constructed from builder and manually") {
        auto from_builder = Points2D({{1.0, 2.0}, {10.0, 20.0}})
                                .with_radii({1.0, 10.0})
                                .with_colors({{0xAA, 0x00, 0x00, 0xCC}, {0x00, 0xBB, 0x00, 0xDD}})
                                .with_labels({"hello", "friend"})
                                .with_class_ids({126, 127})
                                .with_keypoint_ids({1, 2});

        Points2D from_manual;
        from_manual.positions = dalaran::ComponentBatch::from_loggable<dalaran::components::Position2D>(
                                    {{1.0, 2.0}, {10.0, 20.0}},
                                    Points2D::Descriptor_positions
        )
                                    .value_or_throw();
        from_manual.radii = dalaran::ComponentBatch::from_loggable<dalaran::components::Radius>(
                                {1.0, 10.0},
                                Points2D::Descriptor_radii
        )
                                .value_or_throw();
        from_manual.colors = dalaran::ComponentBatch::from_loggable<dalaran::components::Color>(
                                 {{0xAA, 0x00, 0x00, 0xCC}, {0x00, 0xBB, 0x00, 0xDD}},
                                 Points2D::Descriptor_colors
        )
                                 .value_or_throw();
        from_manual.labels = dalaran::ComponentBatch::from_loggable<dalaran::components::Text>(
                                 {"hello", "friend"},
                                 Points2D::Descriptor_labels
        )
                                 .value_or_throw();
        from_manual.keypoint_ids =
            dalaran::ComponentBatch::from_loggable<dalaran::components::KeypointId>(
                {1, 2},
                Points2D::Descriptor_keypoint_ids
            )
                .value_or_throw();
        from_manual.class_ids = dalaran::ComponentBatch::from_loggable<dalaran::components::ClassId>(
                                    {126, 127},
                                    Points2D::Descriptor_class_ids
        )
                                    .value_or_throw();

        test_compare_archetype_serialization(from_manual, from_builder);
    }
}
