"""Log an encoded depth image stored as a 16-bit PNG or RVL file."""

import sys
from pathlib import Path

import dalaran as dl

if len(sys.argv) < 2:
    print(
        f"Usage: {sys.argv[0]} <path_to_depth_image.[png|rvl]>", file=sys.stderr
    )
    sys.exit(1)

depth_path = Path(sys.argv[1])

dl.init("dalaran_example_encoded_depth_image", spawn=True)

depth_png = depth_path.read_bytes()
if depth_path.suffix.lower() == ".png":
    media_type = dl.components.MediaType.PNG
else:
    media_type = dl.components.MediaType.RVL

dl.log(
    "depth/encoded",
    dl.EncodedDepthImage(
        blob=depth_png,
        media_type=media_type,
        meter=0.001,
    ),
)
