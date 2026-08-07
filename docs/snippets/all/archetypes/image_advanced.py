"""Log an image."""

import tempfile

import cv2
import numpy as np
from PIL import Image as PILImage
from PIL import ImageDraw

import dalaran as dl

# Save a transparent PNG to a temporary file.
_, file_path = tempfile.mkstemp(suffix=".png")
image = PILImage.new("RGBA", (300, 200), color=(0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.rectangle((0, 0, 300, 200), outline=(255, 0, 0), width=6)
draw.rounded_rectangle((50, 50, 150, 150), fill=(0, 255, 0), radius=20)
image.save(file_path)


dl.init("dalaran_example_image_advanced")

# Log the image from the file.
dl.log("from_file", dl.EncodedImage(path=file_path))

# Read with Pillow and NumPy, and log the image.
image_data = np.array(PILImage.open(file_path))
dl.log("from_pillow_rgba", dl.Image(image_data))

# Drop the alpha channel from the image.
image_rgb = image_data[..., :3]
dl.log("from_pillow_rgb", dl.Image(image_rgb))

# Read with OpenCV.
image_cv = cv2.imread(file_path)
# OpenCV uses BGR ordering, we need to make this known to Dalaran.
dl.log("from_opencv", dl.Image(image_cv, color_model="BGR"))
