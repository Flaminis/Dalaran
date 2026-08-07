// Log a simple line strip.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_line_strip3d");
    rec.spawn().exit_on_failure();

    dalaran::LineStrip3D linestrip({
        {0.f, 0.f, 0.f},
        {0.f, 0.f, 1.f},
        {1.f, 0.f, 0.f},
        {1.f, 0.f, 1.f},
        {1.f, 1.f, 0.f},
        {1.f, 1.f, 1.f},
        {0.f, 1.f, 0.f},
        {0.f, 1.f, 1.f},
    });
    rec.log("strip", dalaran::LineStrips3D(linestrip));
}
