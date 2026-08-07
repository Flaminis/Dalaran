// Log a batch of oriented bounding boxes.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_box3d_batch");
    rec.spawn().exit_on_failure();

    rec.log(
        "batch",
        dalaran::Boxes3D::from_centers_and_half_sizes(
            {{2.0f, 0.0f, 0.0f}, {-2.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 2.0f}},
            {{2.0f, 2.0f, 1.0f}, {1.0f, 1.0f, 0.5f}, {2.0f, 0.5f, 1.0f}}
        )
            .with_quaternions({
                dalaran::Quaternion::IDENTITY,
                // 45 degrees around Z
                dalaran::Quaternion::from_xyzw(0.0f, 0.0f, 0.382683f, 0.923880f),
            })
            .with_radii({0.025f})
            .with_colors({
                dalaran::Rgba32(255, 0, 0),
                dalaran::Rgba32(0, 255, 0),
                dalaran::Rgba32(0, 0, 255),
            })
            .with_fill_mode(dalaran::FillMode::Solid)
            .with_labels({"red", "green", "blue"})
    );
}
