#include "archetype_test.hpp"

#include <dalaran/archetypes/annotation_context.hpp>

using namespace dalaran::archetypes;

#define TEST_TAG "[annotation_context][archetypes]"

SCENARIO(
    "AnnotationContext archetype's class descriptions can be constructed in various ways and "
    "serialized",
    TEST_TAG
) {
    GIVEN("A annotation context created with various utilities and one manual step by step") {
        dalaran::archetypes::AnnotationContext from_utilities({
            dalaran::datatypes::ClassDescription(1, "hello"),
            dalaran::datatypes::ClassDescription(dalaran::datatypes::AnnotationInfo(1, "hello")),
            dalaran::datatypes::ClassDescription(
                {2, "world", dalaran::datatypes::Rgba32(3, 4, 5)},
                {{17, "head"}, {42, "shoulders"}},
                {
                    {1, 2},
                    {3, 4},
                }
            ),
            dalaran::datatypes::ClassDescription(
                dalaran::datatypes::AnnotationInfo(2, "world", dalaran::datatypes::Rgba32(3, 4, 5)),
                {
                    dalaran::datatypes::AnnotationInfo(17, "head"),
                    dalaran::datatypes::AnnotationInfo(42, "shoulders"),
                },
                {
                    std::pair<uint16_t, uint16_t>(1, 2),
                    std::pair<uint16_t, uint16_t>(3, 4),
                }
            ),
        });

        AnnotationContext manual_archetype;
        std::vector<dalaran::datatypes::ClassDescriptionMapElem> class_map;
        {
            dalaran::datatypes::ClassDescriptionMapElem element;
            dalaran::datatypes::KeypointPair pair;
            dalaran::datatypes::AnnotationInfo keypoint_annotation;

            {
                element.class_id = 1;
                element.class_description.info.id = 1;
                element.class_description.info.color = std::nullopt;
                element.class_description.info.label = "hello";
                class_map.push_back(element);
                class_map.push_back(element);
            }
            {
                std::vector<dalaran::datatypes::AnnotationInfo> keypoint_annotations;
                std::vector<dalaran::datatypes::KeypointPair> keypoint_connections;

                element.class_id = 2;
                element.class_description.info.id = 2;
                element.class_description.info.color = dalaran::datatypes::Rgba32(3, 4, 5);
                element.class_description.info.label = "world";

                keypoint_annotation.id = 17;
                keypoint_annotation.color = std::nullopt;
                keypoint_annotation.label = "head";
                keypoint_annotations.push_back(keypoint_annotation);

                keypoint_annotation.id = 42;
                keypoint_annotation.color = std::nullopt;
                keypoint_annotation.label = "shoulders";
                keypoint_annotations.push_back(keypoint_annotation);

                pair.keypoint0 = 1;
                pair.keypoint1 = 2;
                keypoint_connections.push_back(pair);

                pair.keypoint0 = 3;
                pair.keypoint1 = 4;
                keypoint_connections.push_back(pair);

                element.class_description.keypoint_connections = std::move(keypoint_connections);
                element.class_description.keypoint_annotations = std::move(keypoint_annotations);

                class_map.push_back(element);
                class_map.push_back(element);
            }
        }
        manual_archetype.context = dalaran::ComponentBatch::from_loggable(
                                       dalaran::components::AnnotationContext(class_map),
                                       AnnotationContext::Descriptor_context
        )
                                       .value_or_throw();

        test_compare_archetype_serialization(from_utilities, manual_archetype);
    }
}
