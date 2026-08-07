<!--[metadata]
title = "Live depth sensor"
description = "Stream live RGB + depth from an Intel RealSense sensor into a Dalaran 3D view with a pinhole camera model."
tags = ["2D", "3D", "Live", "Depth", "RealSense"]
thumbnail = "https://static.rerun.io/live_depth_sensor/d3c0392bebe2003d24110a779d6f6748167772d8/480w.png"
thumbnail_dimensions = [480, 360]
-->

Visualize the live-streaming frames from an Intel RealSense depth sensor.

<picture>
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/live_depth_sensor/d3c0392bebe2003d24110a779d6f6748167772d8/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/live_depth_sensor/d3c0392bebe2003d24110a779d6f6748167772d8/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/live_depth_sensor/d3c0392bebe2003d24110a779d6f6748167772d8/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/live_depth_sensor/d3c0392bebe2003d24110a779d6f6748167772d8/1200w.png">
  <img src="https://static.rerun.io/live_depth_sensor/d3c0392bebe2003d24110a779d6f6748167772d8/full.png" alt="Live Depth Sensor example screenshot">
</picture>

This example requires a connected realsense depth sensor.

## Used Dalaran types
[`Pinhole`](https://www.dalaran.dev/docs/reference/types/archetypes/pinhole), [`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d), [`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image), [`DepthImage`](https://www.dalaran.dev/docs/reference/types/archetypes/depth_image)

## Background
The Intel RealSense depth sensor can stream live depth and color data. To visualize this data output, we utilized Dalaran.

## Logging and visualizing with Dalaran

The RealSense sensor captures data in both RGB and depth formats, which are logged using the [`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image) and [`DepthImage`](https://www.dalaran.dev/docs/reference/types/archetypes/depth_image) archetypes, respectively.
Additionally, to provide a 3D view, the visualization includes a pinhole camera using the [`Pinhole`](https://www.dalaran.dev/docs/reference/types/archetypes/pinhole) and [`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d) archetypes.

The visualization in this example were created with the following Dalaran code.

```python
dl.log("realsense", dl.ViewCoordinates.RDF, static=True)  # Visualize the data as RDF
```



### Image

First, the pinhole camera is set using the [`Pinhole`](https://www.dalaran.dev/docs/reference/types/archetypes/pinhole) and [`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d) archetypes. Then, the images captured by the RealSense sensor are logged as an [`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image) object, and they're associated with the time they were taken.



```python
rgb_from_depth = depth_profile.get_extrinsics_to(rgb_profile)
dl.log(
    "realsense/rgb",
    dl.Transform3D(
        translation=rgb_from_depth.translation,
        mat3x3=np.reshape(rgb_from_depth.rotation, (3, 3)),
        relation=dl.TransformRelation.ChildFromParent,
    ),
    static=True,
)
```

```python
dl.log(
    "realsense/rgb/image",
    dl.Pinhole(
        resolution=[rgb_intr.width, rgb_intr.height],
        focal_length=[rgb_intr.fx, rgb_intr.fy],
        principal_point=[rgb_intr.ppx, rgb_intr.ppy],
    ),
    static=True,
)
```
```python
dl.set_time("frame_nr", sequence=frame_nr)
dl.log("realsense/rgb/image", dl.Image(color_image))
```

### Depth image

Just like the RGB images, the RealSense sensor also captures depth data. The depth images are logged as [`DepthImage`](https://www.dalaran.dev/docs/reference/types/archetypes/depth_image) objects and are linked with the time they were captured.

```python
dl.log(
    "realsense/depth/image",
    dl.Pinhole(
        resolution=[depth_intr.width, depth_intr.height],
        focal_length=[depth_intr.fx, depth_intr.fy],
        principal_point=[depth_intr.ppx, depth_intr.ppy],
    ),
    static=True,
)
```
```python
dl.set_time("frame_nr", sequence=frame_nr)
dl.log("realsense/depth/image", dl.DepthImage(depth_image, meter=1.0 / depth_units))
```

## Run the code
To run this example, make sure you have the Dalaran repository checked out and the latest SDK installed:
```bash
pip install --upgrade dalaran-sdk  # install the latest Dalaran SDK
git clone git@github.com:rerun-io/rerun.git  # Clone the repository
cd dalaran
git checkout latest  # Check out the commit matching the latest SDK release
```
Install the necessary libraries specified in the requirements file:
```bash
pip install -e examples/python/live_depth_sensor
```
To experiment with the provided example, simply execute the main Python script:
```bash
python -m live_depth_sensor # run the example
```
If you wish to customize it, explore additional features, or save it use the CLI with the `--help` option for guidance:
```bash
python -m live_depth_sensor --help
```
