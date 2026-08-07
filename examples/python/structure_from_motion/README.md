<!--[metadata]
title = "Structure from motion"
description = "Visualize a sparse 3D reconstruction from COLMAP: camera frames, estimated poses, and an accumulating point cloud."
tags = ["2D", "3D", "COLMAP", "Pinhole camera", "Time series"]
thumbnail = "https://static.rerun.io/structure-from-motion/af24e5e8961f46a9c10399dbc31b6611eea563b4/480w.png"
thumbnail_dimensions = [480, 480]
channel = "main"
include_in_manifest = true
build_args = ["--dataset=colmap_fiat", "--resize=800x600"]
-->

Visualize a sparse reconstruction by [COLMAP](https://colmap.github.io/index.html), a general-purpose Structure-from-Motion (SfM) and Multi-View Stereo (MVS) pipeline with a graphical and command-line interface

<picture data-inline-viewer="examples/structure_from_motion">
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/structure_from_motion/b17f8824291fa1102a4dc2184d13c91f92d2279c/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/structure_from_motion/b17f8824291fa1102a4dc2184d13c91f92d2279c/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/structure_from_motion/b17f8824291fa1102a4dc2184d13c91f92d2279c/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/structure_from_motion/b17f8824291fa1102a4dc2184d13c91f92d2279c/1200w.png">
  <img src="https://static.rerun.io/structure_from_motion/b17f8824291fa1102a4dc2184d13c91f92d2279c/full.png" alt="Structure From Motion example screenshot">
</picture>

## Background

COLMAP is a general-purpose Structure-from-Motion (SfM) and Multi-View Stereo (MVS) pipeline.
In this example, a short video clip has been processed offline using the COLMAP pipeline.
The processed data was then visualized using Dalaran, which allowed for the visualization of individual camera frames, estimation of camera poses, and creation of point clouds over time.
By using COLMAP in combination with Dalaran, a highly-detailed reconstruction of the scene depicted in the video was generated.

## Used Dalaran types

[`Points2D`](https://www.dalaran.dev/docs/reference/types/archetypes/points2d), [`Points3D`](https://www.dalaran.dev/docs/reference/types/archetypes/points3d), [`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d), [`SeriesLines`](https://www.dalaran.dev/docs/reference/types/archetypes/series_lines), [`Scalars`](https://www.dalaran.dev/docs/reference/types/archetypes/scalars), [`Pinhole`](https://www.dalaran.dev/docs/reference/types/archetypes/pinhole), [`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image), [`TextDocument`](https://www.dalaran.dev/docs/reference/types/archetypes/text_document)

## Logging and visualizing with Dalaran

The visualizations in this example were created with the following Dalaran code:

### Timelines

All data logged using Dalaran in the following sections is connected to a specific frame.
Dalaran assigns a frame id to each piece of logged data, and these frame ids are associated with a [`timeline`](https://www.dalaran.dev/docs/concepts/logging-and-ingestion/timelines).

 ```python
dl.set_time("frame", sequence=frame_idx)
 ```

### Images
The images are logged through the [`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image) to the `camera/image` entity.

```python
dl.log("camera/image", dl.Image(rgb).compress(jpeg_quality=75))
```

### Cameras
The images stem from pinhole cameras located in the 3D world. To visualize the images in 3D, the pinhole projection has
to be logged and the camera pose (this is often referred to as the intrinsics and extrinsics of the camera,
respectively).

The [`Pinhole`](https://www.dalaran.dev/docs/reference/types/archetypes/pinhole) is logged to the `camera/image` entity and defines the intrinsics of the camera.
This defines how to go from the 3D camera frame to the 2D image plane. The extrinsics are logged as an
[`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d) to the `camera` entity.

```python
dl.log(
    "camera",
    dl.Transform3D(
        translation=image.tvec, rotation=dl.Quaternion(xyzw=quat_xyzw), relation=dl.TransformRelation.ChildFromParent
    ),
)
```

```python
dl.log(
    "camera/image",
    dl.Pinhole(
        resolution=[camera.width, camera.height],
        focal_length=camera.params[:2],
        principal_point=camera.params[2:],
    ),
)
```

### Reprojection error
For each image a [`Scalars`](https://www.dalaran.dev/docs/reference/types/archetypes/scalars) archetype containing the average reprojection error of the keypoints is logged to the
`plot/avg_reproj_err` entity.

```python
dl.log("plot/avg_reproj_err", dl.Scalars(np.mean(point_errors)))
```

### 2D points
The 2D image points that are used to triangulate the 3D points are visualized by logging as [`Points2D`](https://www.dalaran.dev/docs/reference/types/archetypes/points2d)
to the `camera/image/keypoints` entity. Note that these keypoints are a child of the
`camera/image` entity, since the points should show in the image plane.

```python
dl.log("camera/image/keypoints", dl.Points2D(visible_xys, colors=[34, 138, 167]))
```

### 3D points
The colored 3D points were added to the visualization by logging the [`Points3D`](https://www.dalaran.dev/docs/reference/types/archetypes/points3d) archetype to the `points` entity.
```python
dl.log("points", dl.Points3D(points, colors=point_colors), dl.AnyValues(error=point_errors))
```

## Run the code
To run this example, make sure you have the Dalaran repository checked out and the latest SDK installed:
```bash
pip install --upgrade dalaran-sdk  # install the latest Dalaran SDK
git clone git@github.com:Flaminis/Dalaran.git  # Clone the repository
cd dalaran
git checkout latest  # Check out the commit matching the latest SDK release
```
Install the necessary libraries specified in the requirements file:
```bash
pip install -e examples/python/structure_from_motion
```
To experiment with the provided example, simply execute the main Python script:
```bash
python -m structure_from_motion # run the example
```
If you wish to customize it, explore additional features, or save it use the CLI with the `--help` option for guidance:
```bash
python -m structure_from_motion --help
```
