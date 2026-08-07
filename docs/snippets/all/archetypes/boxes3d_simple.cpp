// Log a single 3D box.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_box3d");
    rec.spawn().exit_on_failure();

    rec.log("simple", dalaran::Boxes3D::from_half_sizes({{2.f, 2.f, 1.0f}}));
}
