"""Log a simple occupancy grid map."""

import numpy as np

import dalaran as dl

width, height = 64, 64
cell_size = 0.1

# Create a synthetic image with ROS `nav_msgs/OccupancyGrid` cell value
# conventions: -1 (255) unknown, 0 free, 100 occupied.
grid = np.full((height, width), -1, dtype=np.int8)
grid[8:56, 8:56] = 0
grid[20:44, 20:44] = 100

dl.init("dalaran_example_grid_map", spawn=True)

dl.log(
    "world/map",
    dl.GridMap(
        data=grid.tobytes(),
        format=dl.components.ImageFormat(
            width=width,
            height=height,
            color_model="L",
            channel_datatype="U8",
        ),
        cell_size=cell_size,
        translation=[
            -(width * cell_size) / 2.0,
            -(height * cell_size) / 2.0,
            0.0,
        ],
        colormap=dl.components.Colormap.RvizMap,
    ),
)
