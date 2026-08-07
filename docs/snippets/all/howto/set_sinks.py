"""Log some data to a file and a Viewer at the same time."""

import numpy as np

import dalaran as dl

# Initialize the SDK and give our recording a unique name
dl.init("dalaran_example_set_sinks")

dl.set_sinks(
    # Connect to an existing local Viewer or gRPC server.
    dl.GrpcSink(),
    # To host a gRPC server instead, replace the sink above with:
    # dl.GrpcServerSink(),
    # Write data to a `data.rrd` file in the current directory
    dl.FileSink("data.rrd"),
)

# Create some data
SIZE = 10

pos_grid = np.meshgrid(*[np.linspace(-10, 10, SIZE)] * 3)
positions = np.vstack([d.reshape(-1) for d in pos_grid]).T

col_grid = np.meshgrid(*[np.linspace(0, 255, SIZE)] * 3)
colors = np.vstack([c.reshape(-1) for c in col_grid]).astype(np.uint8).T

# Log the data
dl.log(
    # name under which this entity is logged (known as "entity path")
    "my_points",
    # log data as a 3D point cloud archetype
    dl.Points3D(positions, colors=colors, radii=0.5),
)
