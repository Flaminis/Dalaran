// Log a batch of ellipsoids.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_ellipsoid_batch");
    rec.spawn().exit_on_failure();

    // Let's build a snowman!
    float belly_z = 2.5;
    float head_z = 4.5;
    rec.log(
        "batch",
        dalaran::Ellipsoids3D::from_centers_and_half_sizes(
            {
                {0.0f, 0.0f, 0.0f},
                {0.0f, 0.0f, belly_z},
                {0.0f, 0.0f, head_z},
                {-0.6f, -0.77f, head_z},
                {0.6f, -0.77f, head_z},
            },
            {
                {2.0f, 2.0f, 2.0f},
                {1.5f, 1.5f, 1.5f},
                {1.0f, 1.0f, 1.0f},
                {0.15f, 0.15f, 0.15f},
                {0.15f, 0.15f, 0.15f},
            }
        )
            .with_colors({
                dalaran::Rgba32(255, 255, 255),
                dalaran::Rgba32(255, 255, 255),
                dalaran::Rgba32(255, 255, 255),
                dalaran::Rgba32(0, 0, 0),
                dalaran::Rgba32(0, 0, 0),
            })
            .with_fill_mode(dalaran::FillMode::Solid)
    );
}
