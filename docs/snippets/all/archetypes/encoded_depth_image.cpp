//! Log an encoded depth image stored as a 16-bit PNG or RVL file

#include <dalaran.hpp>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace fs = std::filesystem;

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <path_to_depth_image.[png|rvl]>"
                  << std::endl;
        return 1;
    }

    const auto rec =
        dalaran::RecordingStream("dalaran_example_encoded_depth_image");
    rec.spawn().exit_on_failure();

    const auto depth_path = fs::path(argv[1]);
    std::ifstream file(depth_path, std::ios::binary);
    if (!file) {
        std::cerr << "Failed to open encoded depth image: " << depth_path
                  << std::endl;
        return 1;
    }

    std::vector<uint8_t> bytes{
        std::istreambuf_iterator<char>(file),
        std::istreambuf_iterator<char>()
    };
    // Determine media type based on file extension
    dalaran::MediaType media_type;
    if (depth_path.extension() == ".png") {
        media_type = dalaran::MediaType::png();
    } else {
        media_type = dalaran::MediaType::rvl();
    }

    rec.log(
        "depth/encoded",
        dalaran::archetypes::EncodedDepthImage()
            .with_blob(dalaran::components::Blob(
                dalaran::Collection<uint8_t>::take_ownership(std::move(bytes))
            ))
            .with_media_type(media_type)
            .with_meter(0.001f)
    );
}
