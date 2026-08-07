// Log different transforms between three arrows.

#include <dalaran.hpp>

constexpr float TAU = 6.28318530717958647692528676655900577f;

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_transform3d");
    rec.spawn().exit_on_failure();

    auto arrow = dalaran::Arrows3D::from_vectors({{0.0f, 1.0f, 0.0f}})
                     .with_origins({{0.0f, 0.0f, 0.0f}});

    rec.log("base", arrow);

    rec.log(
        "base/translated",
        dalaran::Transform3D::from_translation({1.0f, 0.0f, 0.0f})
    );
    rec.log("base/translated", arrow);

    rec.log(
        "base/rotated_scaled",
        dalaran::Transform3D::from_rotation_scale(
            dalaran::RotationAxisAngle(
                {0.0f, 0.0f, 1.0f},
                dalaran::Angle::radians(TAU / 8.0f)
            ),
            2.0f
        )
    );
    rec.log("base/rotated_scaled", arrow);
}
