// Log some very simple points.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_points3d");
    rec.spawn().exit_on_failure();

    rec.log(
        "points",
        dalaran::Points3D({{0.0f, 0.0f, 0.0f}, {1.0f, 1.0f, 1.0f}})
    );
}
