//! Logs a simple transform hierarchy with named frames.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream(
        "dalaran_example_transform3d_hierarchy_named_frames"
    );
    rec.spawn().exit_on_failure();

    // Define entities with explicit coordinate frames.
    rec.log(
        "sun",
        dalaran::Ellipsoids3D::from_half_sizes({{1.0f, 1.0f, 1.0f}})
            .with_colors(dalaran::Color(255, 200, 10))
            .with_fill_mode(dalaran::FillMode::Solid),
        dalaran::CoordinateFrame("sun_frame")
    );

    rec.log(
        "planet",
        dalaran::Ellipsoids3D::from_half_sizes({{0.4f, 0.4f, 0.4f}})
            .with_colors(dalaran::Color(40, 80, 200))
            .with_fill_mode(dalaran::FillMode::Solid),
        dalaran::CoordinateFrame("planet_frame")
    );

    rec.log(
        "moon",
        dalaran::Ellipsoids3D::from_half_sizes({{0.15f, 0.15f, 0.15f}})
            .with_colors(dalaran::Color(180, 180, 180))
            .with_fill_mode(dalaran::FillMode::Solid),
        dalaran::CoordinateFrame("moon_frame")
    );

    // Define explicit frame relationships.
    rec.log(
        "planet_transform",
        dalaran::Transform3D::from_translation({6.0f, 0.0f, 0.0f})
            .with_child_frame("planet_frame")
            .with_parent_frame("sun_frame")
    );

    rec.log(
        "moon_transform",
        dalaran::Transform3D::from_translation({3.0f, 0.0f, 0.0f})
            .with_child_frame("moon_frame")
            .with_parent_frame("planet_frame")
    );

    // Connect the viewer to the sun's coordinate frame.
    // This is only needed in the absence of blueprints since a default view will typically be created at `/`.
    rec.log_static("/", dalaran::CoordinateFrame("sun_frame"));

    return 0;
}
