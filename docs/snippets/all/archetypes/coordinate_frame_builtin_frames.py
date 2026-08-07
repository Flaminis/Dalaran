"""Demonstrates using explicit `CoordinateFrame` with implicit transforms."""

import dalaran as dl

dl.init("dalaran_example_transform3d_hierarchy", spawn=True)

dl.set_time("time", sequence=0)
dl.log(
    "red_box",
    dl.Boxes3D(half_sizes=[0.5, 0.5, 0.5], colors=[255, 0, 0]),
    # Use Transform3D to place the box, so we actually change the underlying
    # coordinate frame and not just the box's pose.
    dl.Transform3D(translation=[2.0, 0.0, 0.0]),
)
dl.log(
    "blue_box",
    dl.Boxes3D(half_sizes=[0.5, 0.5, 0.5], colors=[0, 0, 255]),
    # Use Transform3D to place the box, so we actually change the underlying
    # coordinate frame and not just the box's pose.
    dl.Transform3D(translation=[-2.0, 0.0, 0.0]),
)
dl.log("point", dl.Points3D([0.0, 0.0, 0.0], radii=0.5))

# Change where the point is located by cycling through its coordinate frame.
for t, frame_id in enumerate(["tf#/red_box", "tf#/blue_box"]):
    dl.set_time("time", sequence=t + 1)  # leave it untouched at t==0.
    dl.log("point", dl.CoordinateFrame(frame_id))
