"""Log and then clear data."""

import dalaran as dl

dl.init("dalaran_example_clear", spawn=True)

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

# Now clear them, one by one on each tick.
for i in range(len(vectors)):
    dl.log(f"arrows/{i}", dl.Clear(recursive=False))  # or `dl.Clear.flat()`
