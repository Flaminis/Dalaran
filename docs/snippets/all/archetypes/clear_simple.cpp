// Log and then clear data.

#include <dalaran.hpp>

#include <cmath>
#include <numeric>
#include <string> // to_string
#include <vector>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_clear");
    rec.spawn().exit_on_failure();

    std::vector<dalaran::Vector3D> vectors = {
        {1.0, 0.0, 0.0},
        {0.0, -1.0, 0.0},
        {-1.0, 0.0, 0.0},
        {0.0, 1.0, 0.0},
    };
    std::vector<dalaran::Position3D> origins = {
        {-0.5, 0.5, 0.0},
        {0.5, 0.5, 0.0},
        {0.5, -0.5, 0.0},
        {-0.5, -0.5, 0.0},
    };
    std::vector<dalaran::Color> colors = {
        {200, 0, 0},
        {0, 200, 0},
        {0, 0, 200},
        {200, 0, 200},
    };

    // Log a handful of arrows.
    for (size_t i = 0; i < vectors.size(); ++i) {
        auto entity_path = "arrows/" + std::to_string(i);
        rec.log(
            entity_path,
            dalaran::Arrows3D::from_vectors(vectors[i])
                .with_origins(origins[i])
                .with_colors(colors[i])
        );
    }

    // Now clear them, one by one on each tick.
    for (size_t i = 0; i < vectors.size(); ++i) {
        auto entity_path = "arrows/" + std::to_string(i);
        rec.log(entity_path, dalaran::Clear::FLAT);
    }
}
