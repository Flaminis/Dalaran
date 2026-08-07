// Log a couple 2D line segments using 2D line strips.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_line_segments2d");
    rec.spawn().exit_on_failure();

    std::vector<std::vector<std::array<float, 2>>> points = {
        {{0.f, 0.f}, {2.f, 1.f}},
        {{4.f, -1.f}, {6.f, 0.f}},
    };
    rec.log("segments", dalaran::LineStrips2D(points));

    // TODO(#5520): log VisualBounds2D
}
