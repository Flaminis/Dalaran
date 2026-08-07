"""Manual use of individual video frame references."""

import sys

import dalaran as dl
import dalaran.blueprint as dlb

if len(sys.argv) < 2:
    # TODO(#7354): Only mp4 is supported for now.
    print(f"Usage: {sys.argv[0]} <path_to_video.[mp4]>")
    sys.exit(1)

dl.init("dalaran_example_asset_video_manual_frames", spawn=True)

# Log video asset which is referred to by frame references.
dl.log("video_asset", dl.AssetVideo(path=sys.argv[1]), static=True)

# Create two entities, showing the same video frozen at different times.
dl.log(
    "frame_1s",
    dl.VideoFrameReference(seconds=1.0, video_reference="video_asset"),
)
dl.log(
    "frame_2s",
    dl.VideoFrameReference(seconds=2.0, video_reference="video_asset"),
)

# Send blueprint that shows two 2D views next to each other.
dl.send_blueprint(
    dlb.Horizontal(
        dlb.Spatial2DView(origin="frame_1s"),
        dlb.Spatial2DView(origin="frame_2s"),
    )
)
