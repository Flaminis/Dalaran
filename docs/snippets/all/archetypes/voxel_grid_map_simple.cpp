// Log a simple sparse voxel grid map.

#include <dalaran.hpp>

#include <array>
#include <vector>

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_voxel_grid_map_simple");
    rec.spawn().exit_on_failure();

    const std::vector<dalaran::components::VoxelIndex> voxel_indices = {
        dalaran::components::VoxelIndex(-1, 0, 0),
        dalaran::components::VoxelIndex(1, 0, 0),
        dalaran::components::VoxelIndex(1, 1, 0),
        dalaran::components::VoxelIndex(3, 0, 0),
        dalaran::components::VoxelIndex(3, 0, 1),
        dalaran::components::VoxelIndex(4, 0, 1),
    };
    const std::vector<dalaran::components::VoxelValue> values = {
        0.0f,
        0.2f,
        0.4f,
        0.6f,
        0.8f,
        1.0f,
    };

    rec.log(
        "world/voxels",
        dalaran::archetypes::VoxelGridMap(
            voxel_indices,
            std::array<float, 3>{0.25f, 0.25f, 0.25f}
        )
            .with_values(values)
            .with_value_range(
                dalaran::components::ValueRange(std::array<double, 2>{0.0, 1.0})
            )
            .with_colormap(dalaran::components::Colormap::Turbo)
            .with_translation({-0.5f, -0.5f, 0.0f})
    );
}
