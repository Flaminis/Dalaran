// Log a batch of cylinders.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_cylinders3d_batch");
    rec.spawn().exit_on_failure();

    rec.log(
        "cylinders",
        dalaran::Cylinders3D::from_lengths_and_radii(
            {0.0f, 2.0f, 4.0f, 6.0f, 8.0f},
            {1.0f, 0.5f, 0.5f, 0.5f, 1.0f}
        )
            .with_colors({
                dalaran::Rgba32(255, 0, 0),
                dalaran::Rgba32(188, 188, 0),
                dalaran::Rgba32(0, 255, 0),
                dalaran::Rgba32(0, 188, 188),
                dalaran::Rgba32(0, 0, 255),
            })
            .with_centers({
                {0.0f, 0.0f, 0.0f},
                {2.0f, 0.0f, 0.0f},
                {4.0f, 0.0f, 0.0f},
                {6.0f, 0.0f, 0.0f},
                {8.0f, 0.0f, 0.0f},
            })
            .with_rotation_axis_angles({
                dalaran::RotationAxisAngle(
                    {1.0f, 0.0f, 0.0f},
                    dalaran::Angle::degrees(0.0)
                ),
                dalaran::RotationAxisAngle(
                    {1.0f, 0.0f, 0.0f},
                    dalaran::Angle::degrees(-22.5)
                ),
                dalaran::RotationAxisAngle(
                    {1.0f, 0.0f, 0.0f},
                    dalaran::Angle::degrees(-45.0)
                ),
                dalaran::RotationAxisAngle(
                    {1.0f, 0.0f, 0.0f},
                    dalaran::Angle::degrees(-67.5)
                ),
                dalaran::RotationAxisAngle(
                    {1.0f, 0.0f, 0.0f},
                    dalaran::Angle::degrees(-90.0)
                ),
            })
    );
}
