#include <dalaran.hpp>
#include <dalaran/demo_utils.hpp>

using namespace dalaran::demo;

int main(int argc, char* argv[]) {
    // Create a new `RecordingStream` which sends data over gRPC to the viewer process.
    const auto rec =
        dalaran::RecordingStream("dalaran_example_quick_start_connect");
    rec.connect_grpc().exit_on_failure();

    // Create some data using the `grid` utility function.
    std::vector<dalaran::Position3D> points =
        grid3d<dalaran::Position3D, float>(-10.f, 10.f, 10);
    std::vector<dalaran::Color> colors =
        grid3d<dalaran::Color, uint8_t>(0, 255, 10);

    // Log the "my_points" entity with our data, using the `Points3D` archetype.
    rec.log(
        "my_points",
        dalaran::Points3D(points).with_colors(colors).with_radii({0.5f})
    );
}
