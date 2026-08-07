// Log a batch of 3D line strips.

#include <dalaran.hpp>

#include <vector>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_line_strip3d_batch");
    rec.spawn().exit_on_failure();

    dalaran::Collection<dalaran::Vec3D> strip1 = {
        {0.f, 0.f, 2.f},
        {1.f, 0.f, 2.f},
        {1.f, 1.f, 2.f},
        {0.f, 1.f, 2.f},
    };
    dalaran::Collection<dalaran::Vec3D> strip2 = {
        {0.f, 0.f, 0.f},
        {0.f, 0.f, 1.f},
        {1.f, 0.f, 0.f},
        {1.f, 0.f, 1.f},
        {1.f, 1.f, 0.f},
        {1.f, 1.f, 1.f},
        {0.f, 1.f, 0.f},
        {0.f, 1.f, 1.f},
    };
    rec.log(
        "strips",
        dalaran::LineStrips3D({strip1, strip2})
            .with_colors({0xFF0000FF, 0x00FF00FF})
            .with_radii({0.025f, 0.005f})
            .with_labels({"one strip here", "and one strip there"})
    );
}
