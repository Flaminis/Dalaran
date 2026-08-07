"""Demonstrates pinhole camera projections with Dalaran blueprints."""

import numpy as np

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_pinhole_projections", spawn=True)

img_height, img_width = 12, 16

# Create a 3D scene with a camera and an image.
dl.log(
    "world/box",
    dl.Boxes3D(centers=[0, 0, 0], half_sizes=[1, 1, 1], colors=[255, 0, 0]),
)
dl.log(
    "world/points",
    dl.Points3D(
        positions=[(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1)],
        colors=[
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 0),
            (255, 0, 255),
        ],
        radii=0.1,
    ),
)
dl.log(
    "camera",
    dl.Transform3D(translation=[0, 3, 0]),
    dl.Pinhole(
        width=img_width,
        height=img_height,
        focal_length=10,
        camera_xyz=dl.ViewCoordinates.LEFT_HAND_Z_UP,
    ),
)
# Create a simple test image.
checkerboard = np.zeros((img_height, img_width, 1), dtype=np.uint8)
checkerboard[
    (np.arange(img_height)[:, None] + np.arange(img_width)) % 2 == 0
] = 255
dl.log("camera/image", dl.Image(checkerboard))

# Use a blueprint to show both 3D and 2D views side by side.
blueprint = dlb.Blueprint(
    dlb.Horizontal(
        # 3D view showing the scene and camera
        dlb.Spatial3DView(
            origin="world",
            name="3D Scene",
            contents=["/**"],
            overrides={
                # Adjust visual size of camera frustum in 3D view for
                # better visibility.
                "camera": dl.Pinhole.from_fields(image_plane_distance=1.0)
            },
        ),
        # 2D projection from angled camera
        dlb.Spatial2DView(
            # Make sure that the origin is at the camera's path.
            origin="camera",
            name="Camera",
            contents=["/**"],  # Add everything, so 3D objects get projected.
        ),
    )
)

dl.send_blueprint(blueprint)
