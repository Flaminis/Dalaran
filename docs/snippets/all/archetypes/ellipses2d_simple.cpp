// Log some simple 2D ellipses.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_ellipses2d");
    rec.spawn().exit_on_failure();

    rec.log(
        "simple",
        dalaran::Ellipses2D::from_centers_and_half_sizes(
            {{0.0f, 0.0f}},
            {{2.0f, 1.0f}}
        )
    );
}
