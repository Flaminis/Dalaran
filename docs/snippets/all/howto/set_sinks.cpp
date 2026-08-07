#include <dalaran.hpp>
#include <dalaran/demo_utils.hpp>

using namespace dalaran::demo;

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_set_sinks");
    rec.set_sinks(
           // Connect to an existing local Viewer or gRPC server.
           dalaran::GrpcSink{},
           // To host a gRPC server instead, replace the sink above with:
           // dalaran::GrpcServerSink{},
           // Write data to a `data.dlr` file in the current directory.
           dalaran::FileSink{"data.dlr"}
    )
        .exit_on_failure();

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
