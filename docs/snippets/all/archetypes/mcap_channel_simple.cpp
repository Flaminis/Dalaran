// Log a simple MCAP channel definition.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_mcap_channel");
    rec.spawn().exit_on_failure();

    const std::vector<dalaran::datatypes::Utf8Pair> metadata = {
        {"frame_id", "camera_link"},
        {"encoding", "bgr8"},
    };

    rec.log(
        "mcap/channels/camera",
        dalaran::archetypes::McapChannel(1, "/camera/image", "cdr")
            .with_metadata(dalaran::KeyValuePairs(metadata))
    );
}
