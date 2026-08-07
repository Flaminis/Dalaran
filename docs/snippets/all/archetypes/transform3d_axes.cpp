// Log different transforms with visualized coordinates axes.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_transform3d_axes");
    rec.spawn().exit_on_failure();

    rec.set_time_sequence("step", 0);

    rec.log("base", dalaran::Transform3D(), dalaran::TransformAxes3D(1.0));

    for (int deg = 0; deg < 360; deg++) {
        rec.set_time_sequence("step", deg);

        rec.log(
            "base/rotated",
            dalaran::Transform3D().with_rotation_axis_angle(
                dalaran::RotationAxisAngle(
                    {1.0f, 1.0f, 1.0f},
                    dalaran::Angle::degrees(static_cast<float>(deg))
                )
            ),
            dalaran::TransformAxes3D(0.5)
        );

        rec.log(
            "base/rotated/translated",
            dalaran::Transform3D().with_translation({2.0f, 0.0f, 0.0f}),
            dalaran::TransformAxes3D(0.5)
        );
    }
}
