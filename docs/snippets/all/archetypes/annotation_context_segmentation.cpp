// Log a segmentation image with annotations.

#include <dalaran.hpp>

#include <algorithm> // fill_n
#include <vector>

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_annotation_context_segmentation");
    rec.spawn().exit_on_failure();

    // create an annotation context to describe the classes
    rec.log_static(
        "segmentation",
        dalaran::AnnotationContext({
            dalaran::AnnotationInfo(1, "red", dalaran::Rgba32(255, 0, 0)),
            dalaran::AnnotationInfo(2, "green", dalaran::Rgba32(0, 255, 0)),
        })
    );

    // create a segmentation image
    const int HEIGHT = 200;
    const int WIDTH = 300;
    std::vector<uint8_t> data(WIDTH * HEIGHT, 0);
    for (auto y = 50; y < 100; ++y) {
        std::fill_n(data.begin() + y * WIDTH + 50, 70, static_cast<uint8_t>(1));
    }
    for (auto y = 100; y < 180; ++y) {
        std::fill_n(
            data.begin() + y * WIDTH + 130,
            150,
            static_cast<uint8_t>(2)
        );
    }

    rec.log(
        "segmentation/image",
        dalaran::SegmentationImage(data.data(), {WIDTH, HEIGHT})
    );
}
