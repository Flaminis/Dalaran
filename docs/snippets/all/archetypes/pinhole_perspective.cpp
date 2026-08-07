// Logs a point cloud and a perspective camera looking at it.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_pinhole_perspective");
    rec.spawn().exit_on_failure();

    const float fov_y = 0.7853982f;
    const float aspect_ratio = 1.7777778f;
    rec.log(
        "world/cam",
        dalaran::Pinhole::from_fov_and_aspect_ratio(fov_y, aspect_ratio)
            .with_camera_xyz(dalaran::components::ViewCoordinates::RUB)
            .with_image_plane_distance(0.1f)
            .with_color(dalaran::Color(255, 128, 0))
            .with_line_width(0.003f)
    );

    rec.log(
        "world/points",
        dalaran::Points3D(
            {{0.0f, 0.0f, -0.5f}, {0.1f, 0.1f, -0.5f}, {-0.1f, -0.1f, -0.5f}}
        )
            .with_radii({0.025f})
    );
}
