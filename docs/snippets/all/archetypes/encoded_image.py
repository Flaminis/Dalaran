"""Create and log an image."""

from pathlib import Path

import dalaran as dl

image_file_path = Path(__file__).parent / "ferris.png"

dl.init("dalaran_example_encoded_image", spawn=True)

dl.log("image", dl.EncodedImage(path=image_file_path))
