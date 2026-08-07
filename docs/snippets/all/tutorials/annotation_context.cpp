#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_annotation_context_connections");
    rec.spawn().exit_on_failure();

    // Annotation context with two classes, using two labeled classes, of which ones defines a
    // color.
    rec.log_static(
        "masks",
        dalaran::AnnotationContext({
            dalaran::AnnotationInfo(0, "Background"),
            dalaran::AnnotationInfo(1, "Person", dalaran::Rgba32(255, 0, 0)),
        })
    );

    // Annotation context with simple keypoints & keypoint connections.
    std::vector<dalaran::AnnotationInfo> keypoint_annotations;
    for (uint16_t i = 0; i < 10; ++i) {
        keypoint_annotations.push_back(dalaran::AnnotationInfo(
            i,
            dalaran::Rgba32(0, static_cast<uint8_t>(28 * i), 0)
        ));
    }

    std::vector<dalaran::KeypointPair> keypoint_connections;
    for (uint16_t i = 0; i < 9; ++i) {
        keypoint_connections.push_back(dalaran::KeypointPair(i, i + 1));
    }

    rec.log_static(
        "detections", // Applies to all entities below "detections".
        dalaran::AnnotationContext({dalaran::ClassDescription(
            dalaran::AnnotationInfo(0, "Snake"),
            keypoint_annotations,
            keypoint_connections
        )})
    );
}
