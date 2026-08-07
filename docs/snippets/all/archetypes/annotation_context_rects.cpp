// Log an annotation context to assign a label and color to each class

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_annotation_context_rects");
    rec.spawn().exit_on_failure();

    // Log an annotation context to assign a label and color to each class
    rec.log_static(
        "/",
        dalaran::AnnotationContext({
            dalaran::AnnotationInfo(1, "red", dalaran::Rgba32(255, 0, 0)),
            dalaran::AnnotationInfo(2, "green", dalaran::Rgba32(0, 255, 0)),
        })
    );

    // Log a batch of 2 rectangles with different class IDs
    rec.log(
        "detections",
        dalaran::Boxes2D::from_mins_and_sizes(
            {{-2.0f, -2.0f}, {0.0f, 0.f}},
            {{3.0f, 3.0f}, {2.0f, 2.0f}}
        )
            .with_class_ids({1, 2})
    );
}
