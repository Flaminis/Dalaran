// Log a simple colored triangle.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_mesh3d");
    rec.spawn().exit_on_failure();

    dalaran::Position3D vertex_positions[3] = {
        {0.0f, 0.0f, 0.0f},
        {1.0f, 0.0f, 0.0f},
        {0.0f, 1.0f, 0.0f},
    };
    dalaran::Color vertex_colors[3] = {
        {255, 0, 0},
        {0, 255, 0},
        {0, 0, 255},
    };

    rec.log(
        "triangle",
        dalaran::Mesh3D(vertex_positions)
            .with_vertex_normals({{0.0f, 0.0f, 1.0f}})
            .with_vertex_colors(vertex_colors)
    );
}
