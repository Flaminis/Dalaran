// Log a video asset using automatically determined frame references.

#include <dalaran.hpp>

#include <iostream>

using namespace std::chrono_literals;

int main(int argc, char* argv[]) {
    if (argc < 2) {
        // TODO(#7354): Only mp4 is supported for now.
        std::cerr << "Usage: " << argv[0] << " <path_to_video.[mp4]>"
                  << std::endl;
        return 1;
    }

    const auto path = argv[1];

    const auto rec =
        dalaran::RecordingStream("dalaran_example_asset_video_auto_frames");
    rec.spawn().exit_on_failure();

    // Log video asset which is referred to by frame references.
    auto video_asset = dalaran::AssetVideo::from_file(path).value_or_throw();
    rec.log_static("video", video_asset);

    // Send automatically determined video frame timestamps.
    std::vector<std::chrono::nanoseconds> frame_timestamps_ns =
        video_asset.read_frame_timestamps_nanos().value_or_throw();
    // Note timeline values don't have to be the same as the video timestamps.
    auto time_column = dalaran::TimeColumn::from_durations(
        "video_time",
        dalaran::borrow(frame_timestamps_ns)
    );

    std::vector<dalaran::components::VideoTimestamp> video_timestamps(
        frame_timestamps_ns.size()
    );
    for (size_t i = 0; i < frame_timestamps_ns.size(); i++) {
        video_timestamps[i] =
            dalaran::components::VideoTimestamp(frame_timestamps_ns[i]);
    }

    rec.send_columns(
        "video",
        time_column,
        dalaran::VideoFrameReference()
            .with_many_timestamp(dalaran::borrow(video_timestamps))
            .columns()
    );
}
