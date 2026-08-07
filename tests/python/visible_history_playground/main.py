"""Playground to test the visible history feature."""

from __future__ import annotations

import argparse
import datetime
import math

import numpy as np

import dalaran as dl

parser = argparse.ArgumentParser(description=__doc__)
dl.script_add_args(parser)
args = parser.parse_args()
dl.script_setup(args, "dalaran_example_visible_history_playground")

dl.log("bbox", dl.Boxes2D(centers=[50, 3.5], half_sizes=[50, 4.5], colors=[255, 0, 0]), static=True)
dl.log("transform", dl.Transform3D(translation=[0, 0, 0]))
dl.log("some/nested/pinhole", dl.Pinhole(focal_length=3, width=3, height=3), static=True)

dl.log("3dworld/depthimage/pinhole", dl.Pinhole(focal_length=20, width=100, height=10), static=True)
dl.log("3dworld/image", dl.Transform3D(translation=[0, 1, 0]), static=True)
dl.log("3dworld/image/pinhole", dl.Pinhole(focal_length=20, width=100, height=10), static=True)

date_offset = int(datetime.datetime(year=2023, month=1, day=1).timestamp())

for i in range(100):
    dl.set_time("temporal_100day_span", duration=i * 24 * 3600)
    dl.set_time("temporal_100s_span", duration=i)
    dl.set_time("temporal_100ms_span", duration=i / 1000)
    dl.set_time("temporal_100us_span", duration=i / 1000000)

    dl.set_time("temporal_100day_span_date_offset", duration=date_offset + i * 24 * 3600)
    dl.set_time("temporal_100s_span_date_offset", duration=date_offset + i)
    dl.set_time("temporal_100ms_span_date_offset", duration=date_offset + i / 1000)
    dl.set_time("temporal_100us_span_date_offset", duration=date_offset + i / 1000000)

    dl.set_time("temporal_100day_span_zero_centered", duration=(i - 50) * 24 * 3600)
    dl.set_time("temporal_100s_zero_centered", duration=i - 50)
    dl.set_time("temporal_100ms_zero_centered", duration=(i - 50) / 1000)
    dl.set_time("temporal_100us_zero_centered", duration=(i - 50) / 1000000)

    dl.set_time("sequence", sequence=i)
    dl.set_time("sequence_zero_centered", sequence=(i - 50))
    dl.set_time("sequence_10k_offset", sequence=10000 + i)
    dl.set_time("sequence_10k_neg_offset", sequence=-10000 + i)

    dl.log("world/data/nested/point", dl.Points2D([[i, 0], [i, 1]], radii=0.4))
    dl.log("world/data/nested/point2", dl.Points2D([i, 2], radii=0.4))
    dl.log("world/data/nested/box", dl.Boxes2D(centers=[i, 1], half_sizes=[0.5, 0.5]))
    dl.log("world/data/nested/arrow", dl.Arrows3D(origins=[i, 4, 0], vectors=[0, 1.7, 0]))
    dl.log(
        "world/data/nested/linestrip",
        dl.LineStrips2D([[[i - 0.4, 6], [i + 0.4, 6], [i - 0.4, 7], [i + 0.4, 7]], [[i - 0.2, 6.5], [i + 0.2, 6.5]]]),
    )

    dl.log("world/data/nested/transformed", dl.Transform3D(translation=[i, 0, 0]))
    dl.log("world/data/nested/transformed/point", dl.Boxes2D(centers=[0, 3], half_sizes=[0.5, 0.5]))

    dl.log("text_log", dl.TextLog(f"hello {i}"))
    dl.log("scalar", dl.Scalars(math.sin(i / 100 * 2 * math.pi)))

    depth_image = 100 * np.ones((10, 100), dtype=np.float32)
    depth_image[:, i] = 50
    dl.log("3dworld/depthimage/pinhole/data", dl.DepthImage(depth_image, meter=100))

    image = 100 * np.ones((10, 100, 3), dtype=np.uint8)
    image[:, i, :] = [255, 0, 0]
    dl.log("3dworld/image/pinhole/data", dl.Image(image))

    x_coord = (i - 50) / 5
    dl.log(
        "3dworld/mesh",
        dl.Mesh3D(
            vertex_positions=[[x_coord, 2, 0], [x_coord, 2, 1], [x_coord, 3, 0]],
            vertex_colors=[[0, 0, 255], [0, 255, 0], [255, 0, 0]],
        ),
    )
