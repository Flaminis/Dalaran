#!/usr/bin/env python3
"""A test series for view coordinates."""

from __future__ import annotations

import argparse

import numpy as np
import numpy.typing as npt

import dalaran as dl  # pip install dalaran-sdk

parser = argparse.ArgumentParser(description="Logs rich data using the Dalaran SDK.")
dl.script_add_args(parser)
args = parser.parse_args()

dl.script_setup(args, "dalaran_example_view_coordinates")

# Log sphere of colored points to make it easier to orient ourselves.
# See https://math.stackexchange.com/a/1586185
num_points = 5000
radius = 8
lamd = np.arccos(2 * np.random.rand(num_points) - 1) - np.pi / 2
phi = np.random.rand(num_points) * 2 * np.pi
x = np.cos(lamd) * np.cos(phi)
y = np.cos(lamd) * np.sin(phi)
z = np.sin(lamd)
unit_sphere_positions = np.transpose([x, y, z])
dl.log("world/points", dl.Points3D(unit_sphere_positions * radius, colors=np.abs(unit_sphere_positions), radii=0.01))

# RGB image that indicates orientation:
rgb = np.zeros((50, 100, 3))
rgb[0:3, 0:3] = [255, 255, 255]
rgb[3:25, 0:3] = [0, 255, 0]
rgb[0:3, 3:25] = [255, 0, 0]

# Depth image for testing depth cloud:
# depth = np.ones((50, 100)) * 0.5
x, y = np.meshgrid(np.arange(0, 100), np.arange(0, 50))
depth = 0.5 + 0.005 * x + 0.25 * np.sin(3.14 * y / 50 / 2)


dl.log("world", dl.ViewCoordinates.RIGHT_HAND_Z_UP)


def log_camera(origin: npt.ArrayLike, label: str, xyz: dl.components.ViewCoordinates, forward: npt.ArrayLike) -> None:
    [height, width, _channels] = rgb.shape
    f_len = (height * width) ** 0.5
    cam_path = f"world/{label}"
    pinhole_path = f"{cam_path}/{label}"
    dl.log(f"{cam_path}/indicator", dl.Points3D([0, 0, 0], colors=[255, 255, 255], labels=label))
    dl.log(cam_path, dl.Transform3D(translation=origin))
    dl.log(cam_path + "/arrow", dl.Arrows3D(origins=[0, 0, 0], vectors=forward, colors=[255, 255, 255], radii=0.025))
    dl.log(
        pinhole_path,
        dl.Pinhole(
            width=width,
            height=height,
            focal_length=f_len,
            principal_point=[width * 3 / 4, height * 3 / 4],  # test offset principal point
            camera_xyz=xyz,
        ),
    )
    dl.log(f"{pinhole_path}/rgb", dl.Image(rgb))
    dl.log(f"{pinhole_path}/depth", dl.DepthImage(depth, meter=1.0))


# Log a series of pinhole cameras only differing by their view coordinates and some offset.
# Not all possible, but a fair sampling.

s = 3  # spacing

log_camera([0, 0, s], "RUB", dl.ViewCoordinates.RUB, forward=[0, 0, -1])

# All right-handed permutations of RDF:
log_camera([s, -s, 0], "RDF", dl.ViewCoordinates.RDF, forward=[0, 0, 1])
log_camera([s, 0, 0], "FRD", dl.ViewCoordinates.FRD, forward=[1, 0, 0])
log_camera([s, s, 0], "DFR", dl.ViewCoordinates.DFR, forward=[0, 1, 0])

# All right-handed permutations of LUB:
log_camera([0, -s, 0], "ULB", dl.ViewCoordinates.ULB, forward=[0, 0, -1])
log_camera([0, 0, 0], "LBU", dl.ViewCoordinates.LBU, forward=[0, -1, 0])
log_camera([0, s, 0], "BUL", dl.ViewCoordinates.BUL, forward=[-1, 0, 0])

# All permutations of LUF:
log_camera([-s, -s, 0], "LUF", dl.ViewCoordinates.LUF, forward=[0, 0, 1])
log_camera([-s, 0, 0], "FLU", dl.ViewCoordinates.FLU, forward=[1, 0, 0])
log_camera([-s, s, 0], "UFL", dl.ViewCoordinates.UFL, forward=[0, 1, 0])


dl.script_teardown(args)
