#include "../error_check.hpp"
#include "archetype_test.hpp"

#include <dalaran/archetypes/depth_image.hpp>
#include <dalaran/archetypes/segmentation_image.hpp>
#include <dalaran/components/blob.hpp>

using namespace dalaran::archetypes;
using namespace dalaran::datatypes;

#define TEST_TAG "[image][archetypes]"

template <typename ImageType>
void run_image_tests() {
    GIVEN("a vector of u8 data") {
        std::vector<uint8_t> data(10 * 10, 0);
        ImageType reference_image;
        reference_image.buffer = dalaran::ComponentBatch::from_loggable(
                                     dalaran::components::ImageBuffer(data),
                                     ImageType::Descriptor_buffer
        )
                                     .value_or_throw();
        reference_image.format = dalaran::ComponentBatch::from_loggable(
                                     dalaran::components::ImageFormat({10, 10}, ChannelDatatype::U8),
                                     ImageType::Descriptor_format
        )
                                     .value_or_throw();

        THEN("no error occurs on image construction from a pointer") {
            auto image_from_ptr =
                check_logged_error([&] { return ImageType(data.data(), {10, 10}); });
            AND_THEN("serialization succeeds") {
                test_compare_archetype_serialization(image_from_ptr, reference_image);
            }
        }
        THEN("no error occurs on image construction from a collection") {
            auto image_from_collection =
                check_logged_error([&] { return ImageType(dalaran::borrow(data), {10, 10}); });
            AND_THEN("serialization succeeds") {
                test_compare_archetype_serialization(image_from_collection, reference_image);
            }
        }

        THEN("no error occurs on image construction from an untyped pointer") {
            const void* ptr = reinterpret_cast<const void*>(data.data());
            auto image_from_ptr =
                check_logged_error([&] { return ImageType(ptr, {10, 10}, ChannelDatatype::U8); });
            AND_THEN("serialization succeeds") {
                test_compare_archetype_serialization(image_from_ptr, reference_image);
            }
        }
    }
}

SCENARIO("Depth archetype image can be created." TEST_TAG) {
    run_image_tests<DepthImage>();
}

SCENARIO("Segmentation archetype image can be created from tensor data." TEST_TAG) {
    run_image_tests<SegmentationImage>();
}
