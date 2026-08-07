#include "archetype_test.hpp"

#include <dalaran/archetypes/mesh3d.hpp>

using namespace dalaran::archetypes;
using namespace dalaran::components;

#define TEST_TAG "[mesh3d][archetypes]"

SCENARIO(
    "Mesh3D archetype can be serialized with the same result for manually built instances and "
    "the builder pattern",
    TEST_TAG
) {
    GIVEN("Constructed from builder and manually") {
        auto from_builder =
            Mesh3D({{1.0, 2.0, 3.0}, {10.0, 20.0, 30.0}})
                .with_vertex_normals({{4.0, 5.0, 6.0}, {40.0, 50.0, 60.0}})
                .with_vertex_colors({{0xAA, 0x00, 0x00, 0xCC}, {0x00, 0xBB, 0x00, 0xDD}})
                .with_triangle_indices({{1, 2, 3}, {4, 5, 6}})
                .with_albedo_factor(0xEE112233)
                .with_class_ids({126, 127});

        Mesh3D from_manual;
        from_manual.vertex_positions =
            dalaran::ComponentBatch::from_loggable<dalaran::components::Position3D>(
                {{1.0, 2.0, 3.0}, {10.0, 20.0, 30.0}},
                Mesh3D::Descriptor_vertex_positions
            )
                .value_or_throw();
        from_manual.vertex_normals =
            dalaran::ComponentBatch::from_loggable<dalaran::components::Vector3D>(
                {{4.0, 5.0, 6.0}, {40.0, 50.0, 60.0}},
                Mesh3D::Descriptor_vertex_normals
            )
                .value_or_throw();
        from_manual.vertex_colors = dalaran::ComponentBatch::from_loggable<dalaran::components::Color>(
                                        {{0xAA, 0x00, 0x00, 0xCC}, {0x00, 0xBB, 0x00, 0xDD}},
                                        Mesh3D::Descriptor_vertex_colors
        )
                                        .value_or_throw();
        from_manual.triangle_indices =
            dalaran::ComponentBatch::from_loggable<dalaran::components::TriangleIndices>(
                {{1, 2, 3}, {4, 5, 6}},
                Mesh3D::Descriptor_triangle_indices
            )
                .value_or_throw();
        from_manual.albedo_factor = dalaran::ComponentBatch::from_loggable(
                                        dalaran::components::AlbedoFactor({0xEE, 0x11, 0x22, 0x33}),
                                        Mesh3D::Descriptor_albedo_factor
        )
                                        .value_or_throw();
        from_manual.class_ids = dalaran::ComponentBatch::from_loggable<dalaran::components::ClassId>(
                                    {126, 127},
                                    Mesh3D::Descriptor_class_ids
        )
                                    .value_or_throw();

        test_compare_archetype_serialization(from_manual, from_builder);
    }
}
