// Log a simple 3D box with a regular & instance pose transform.

#include <dalaran.hpp>
#include <dalaran/demo_utils.hpp>

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_instance_pose3d_combined");
    rec.set_time_sequence("frame", 0);

    // Log a box and points further down in the hierarchy.
    rec.log("world/box", dalaran::Boxes3D::from_half_sizes({{1.0, 1.0, 1.0}}));
    rec.log(
        "world/box/points",
        dalaran::Points3D(
            dalaran::demo::grid3d<dalaran::Position3D, float>(-10.0f, 10.0f, 10)
        )
    );

    for (int i = 0; i < 180; ++i) {
        rec.set_time_sequence("frame", i);

        // Log a regular transform which affects both the box and the points.
        rec.log(
            "world/box",
            dalaran::Transform3D::from_rotation(dalaran::RotationAxisAngle{
                {0.0f, 0.0f, 1.0f},
                dalaran::Angle::degrees(static_cast<float>(i) * 2.0f)
            })
        );

        // Log an instance pose which affects only the box.
        rec.log(
            "world/box",
            dalaran::InstancePoses3D().with_translations(
                {{0.0f,
                  0.0f,
                  std::abs(static_cast<float>(i) * 0.1f - 5.0f) - 5.0f}}
            )
        );
    }
}
