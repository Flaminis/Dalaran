// Log different transforms between three arrows.

#include <dalaran.hpp>

constexpr float TAU = 6.28318530717958647692528676655900577f;

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_transform3d_hierarchy");
    rec.spawn().exit_on_failure();

    // TODO(#5521): log two views as in the python example

    rec.set_time_duration_secs("sim_time", 0.0);

    // Planetary motion is typically in the XY plane.
    rec.log_static("/", dalaran::ViewCoordinates::RIGHT_HAND_Z_UP);

    // Setup spheres, all are in the center of their own space:
    rec.log(
        "sun",
        dalaran::Ellipsoids3D::from_centers_and_half_sizes(
            {{0.0f, 0.0f, 0.0f}},
            {{1.0f, 1.0f, 1.0f}}
        )
            .with_colors(dalaran::Color(255, 200, 10))
            .with_fill_mode(dalaran::FillMode::Solid)
    );

    rec.log(
        "sun/planet",
        dalaran::Ellipsoids3D::from_centers_and_half_sizes(
            {{0.0f, 0.0f, 0.0f}},
            {{0.4f, 0.4f, 0.4f}}
        )
            .with_colors(dalaran::Color(40, 80, 200))
            .with_fill_mode(dalaran::FillMode::Solid)
    );

    rec.log(
        "sun/planet/moon",
        dalaran::Ellipsoids3D::from_centers_and_half_sizes(
            {{0.0f, 0.0f, 0.0f}},
            {{0.15f, 0.15f, 0.15f}}
        )
            .with_colors(dalaran::Color(180, 180, 180))
            .with_fill_mode(dalaran::FillMode::Solid)
    );

    // Draw fixed paths where the planet & moon move.
    float d_planet = 6.0f;
    float d_moon = 3.0f;
    std::vector<std::array<float, 3>> planet_path, moon_path;
    for (int i = 0; i <= 100; i++) {
        float angle = static_cast<float>(i) * 0.01f * TAU;
        float circle_x = std::sin(angle);
        float circle_y = std::cos(angle);
        planet_path.push_back({circle_x * d_planet, circle_y * d_planet, 0.0f});
        moon_path.push_back({circle_x * d_moon, circle_y * d_moon, 0.0f});
    }
    rec.log(
        "sun/planet_path",
        dalaran::LineStrips3D(dalaran::LineStrip3D(planet_path))
    );
    rec.log(
        "sun/planet/moon_path",
        dalaran::LineStrips3D(dalaran::LineStrip3D(moon_path))
    );

    // Movement via transforms.
    for (int i = 0; i < 6 * 120; i++) {
        float time = static_cast<float>(i) / 120.0f;
        rec.set_time_duration_secs("sim_time", time);
        float r_moon = time * 5.0f;
        float r_planet = time * 2.0f;

        rec.log(
            "sun/planet",
            dalaran::Transform3D::from_translation_rotation(
                {std::sin(r_planet) * d_planet,
                 std::cos(r_planet) * d_planet,
                 0.0f},
                dalaran::RotationAxisAngle{
                    {1.0, 0.0f, 0.0f},
                    dalaran::Angle::degrees(20.0f),
                }
            )
        );
        rec.log(
            "sun/planet/moon",
            dalaran::Transform3D::from_translation(
                {std::cos(r_moon) * d_moon, std::sin(r_moon) * d_moon, 0.0f}
            )
                .with_relation(dalaran::TransformRelation::ChildFromParent)
        );
    }
}
