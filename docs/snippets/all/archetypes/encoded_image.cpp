// Create and log a image.

#include <dalaran.hpp>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>

namespace fs = std::filesystem;

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_encoded_image");
    rec.spawn().exit_on_failure();

    fs::path image_filepath = fs::path(__FILE__).parent_path() / "ferris.png";

    rec.log(
        "image",
        dalaran::EncodedImage::from_file(image_filepath).value_or_throw()
    );
}
