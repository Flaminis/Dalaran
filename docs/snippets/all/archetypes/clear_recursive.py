"""Log and then clear data recursively."""

import dalaran as dl

dl.init("dalaran_example_clear_recursive", spawn=True)

vectors = [(1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
origins = [
    (-0.5, 0.5, 0.0),
    (0.5, 0.5, 0.0),
    (0.5, -0.5, 0.0),
    (-0.5, -0.5, 0.0),
]
colors = [(200, 0, 0), (0, 200, 0), (0, 0, 200), (200, 0, 200)]

# Log a handful of arrows.
for i, (vector, origin, color) in enumerate(
    zip(vectors, origins, colors, strict=False)
):
    dl.log(
        f"arrows/{i}", dl.Arrows3D(vectors=vector, origins=origin, colors=color)
    )

# Now clear all of them at once.
dl.log("arrows", dl.Clear(recursive=True))  # or `dl.Clear.recursive()`
