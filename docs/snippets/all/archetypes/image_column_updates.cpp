//! Update an image over time, in a single operation.
//!
//! This is semantically equivalent to the `image_row_updates` example, albeit much faster.

#include <numeric>
#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    auto rec = dalaran::RecordingStream("dalaran_example_image_column_updates");
    rec.spawn().exit_on_failure();

    // Timeline on which the images are distributed.
    std::vector<int64_t> times(20);
    std::iota(times.begin(), times.end(), 0);

    // Create a batch of images with a moving rectangle.
    const size_t width = 300, height = 200;
    std::vector<uint8_t> images(times.size() * height * width * 3, 0);
    for (size_t t = 0; t < times.size(); ++t) {
        for (size_t y = 0; y < height; ++y) {
            for (size_t x = 0; x < width; ++x) {
                size_t idx = (t * height * width + y * width + x) * 3;
                images[idx + 2] = 255; // Blue background
                if (y >= 50 && y < 150 && x >= t * 10 && x < t * 10 + 100) {
                    images[idx + 1] = 255; // Turquoise rectangle
                }
            }
        }
    }

    // Log the ImageFormat and indicator once, as static.
    auto format = dalaran::components::ImageFormat(
        {width, height},
        dalaran::ColorModel::RGB,
        dalaran::ChannelDatatype::U8
    );
    rec.log_static("images", dalaran::Image::update_fields().with_format(format));

    // Split up the image data into several components referencing the underlying data.
    const size_t image_size_in_bytes = width * height * 3;
    std::vector<dalaran::ImageBuffer> image_data(times.size());
    for (size_t i = 0; i < times.size(); ++i) {
        image_data[i] = dalaran::borrow(
            images.data() + i * image_size_in_bytes,
            image_size_in_bytes
        );
    }

    // Send all images at once.
    rec.send_columns(
        "images",
        dalaran::TimeColumn::from_sequence("step", std::move(times)),
        dalaran::Image().with_many_buffer(std::move(image_data)).columns()
    );
}
