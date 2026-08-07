"""Log a simple 3D asset."""

import sys

import dalaran as dl

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <path_to_asset.[gltf|glb|obj|stl]>")
    sys.exit(1)

dl.init("dalaran_example_asset3d", spawn=True)

dl.log(
    "world", dl.ViewCoordinates.RIGHT_HAND_Z_UP, static=True
)  # Set the 3D view's up direction
dl.log("world/asset", dl.Asset3D(path=sys.argv[1]))
