<!--[metadata]
title = "nuScenes"
description = "Visualize the nuScenes self-driving dataset: 6 cameras, lidar, radar, GPS, IMU, and 3D boxes on one timeline."
tags = ["Lidar", "3D", "2D", "Object detection", "Pinhole camera", "Blueprint"]
thumbnail = "https://static.rerun.io/nuscenes_dataset/3724a84d6e95f15a71db2ccc443fb67bfae58843/480w.png"
thumbnail_dimensions = [480, 301]
channel = "release"
include_in_manifest = true
build_args = ["--seconds=5"]
-->

Visualize the [nuScenes dataset](https://www.nuscenes.org/) including lidar, radar, images, and bounding boxes data.

<picture>
  <img src="https://static.rerun.io/nuscenes_dataset/3724a84d6e95f15a71db2ccc443fb67bfae58843/full.png" alt="">
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/nuscenes_dataset/3724a84d6e95f15a71db2ccc443fb67bfae58843/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/nuscenes_dataset/3724a84d6e95f15a71db2ccc443fb67bfae58843/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/nuscenes_dataset/3724a84d6e95f15a71db2ccc443fb67bfae58843/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/nuscenes_dataset/3724a84d6e95f15a71db2ccc443fb67bfae58843/1200w.png">
</picture>

## Used Dalaran types
[`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d), [`Points3D`](https://www.dalaran.dev/docs/reference/types/archetypes/points3d), [`Boxes3D`](https://www.dalaran.dev/docs/reference/types/archetypes/boxes3d), [`Pinhole`](https://www.dalaran.dev/docs/reference/types/archetypes/pinhole), [`EncodedImage`](https://www.dalaran.dev/docs/reference/types/archetypes/encoded_image)

## Background
This example demonstrates the ability to read and visualize scenes from the nuScenes dataset, which is a public large-scale dataset specifically designed for autonomous driving.
The scenes in this dataset encompass data collected from a comprehensive suite of sensors on autonomous vehicles.
These include 6 cameras, 1 LIDAR, 5 RADAR, GPS and IMU sensors.
Consequently, the dataset provides information about the vehicle's pose, the images captured, the recorded sensor data and the results of object detection at any given moment.


## Logging and visualizing with Dalaran

The visualizations in this example were created with the following Dalaran code:

### Sensor calibration

First, pinhole cameras and sensor poses are initialized to offer a 3D view and camera perspective. This is achieved using the [`Pinhole`](https://www.dalaran.dev/docs/reference/types/archetypes/pinhole) and [`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d) archetypes.

```python
dl.log(
    f"world/ego_vehicle/{sensor_name}",
    dl.Transform3D(
        translation=calibrated_sensor["translation"],
        rotation=dl.Quaternion(xyzw=rotation_xyzw),
        relation=dl.TransformRelation.ParentFromChild,
    ),
    static=True,
)
```

```python
dl.log(
    f"world/ego_vehicle/{sensor_name}",
    dl.Pinhole(
        image_from_camera=calibrated_sensor["camera_intrinsic"],
        width=sample_data["width"],
        height=sample_data["height"],
    ),
    static=True,
)
```

### Timelines

All data logged using Dalaran in the following sections is initially connected to a specific time.
Dalaran assigns a timestamp to each piece of logged data, and these timestamps are associated with [`timelines`](https://www.dalaran.dev/docs/concepts/logging-and-ingestion/timelines).

```python
dl.set_time("timestamp", timestamp=sample_data["timestamp"] * 1e-6)
```


### Vehicle pose

As the vehicle is moving, its pose needs to be updated. Consequently, the positions of pinhole cameras and sensors must also be adjusted using [`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d).
```python
dl.log(
    "world/ego_vehicle",
    dl.Transform3D(
        translation=ego_pose["translation"],
        rotation=dl.Quaternion(xyzw=rotation_xyzw),
        relation=dl.TransformRelation.ParentFromChild,
    ),
)
```

#### GPS data

GPS data is calculated from the scene's reference coordinates and the transformations (starting map point + odometry).
The GPS coordinates are logged as [`GeoPoints`](https://www.dalaran.dev/docs/reference/types/archetypes/geo_points).

```python
dl.log(
    "world/ego_vehicle",
    dl.GeoPoints([[lat, long]]),
)
```

### LiDAR data
LiDAR data is logged as [`Points3D`](https://www.dalaran.dev/docs/reference/types/archetypes/points3d) archetype.
```python
dl.log(f"world/ego_vehicle/{sensor_name}", dl.Points3D(points, colors=point_colors))
```

### Camera data
Camera data is logged as encoded images using [`EncodedImage`](https://www.dalaran.dev/docs/reference/types/archetypes/encoded_image).
```python
dl.log(f"world/ego_vehicle/{sensor_name}", dl.EncodedImage(path=data_file_path))
```

### Radar data
Radar data is logged similar to LiDAR data, as [`Points3D`](https://www.dalaran.dev/docs/reference/types/archetypes/points3d).
```python
dl.log(f"world/ego_vehicle/{sensor_name}", dl.Points3D(points, colors=point_colors))
```

### Annotations

Annotations are logged as [`Boxes3D`](https://www.dalaran.dev/docs/reference/types/archetypes/boxes3d), containing details such as object positions, sizes, and rotation.
```python
dl.log(
    "world/anns",
    dl.Boxes3D(
        sizes=sizes,
        centers=centers,
        quaternions=quaternions,
        class_ids=class_ids,
        fill_mode=dl.components.FillMode.Solid,
    ),
)
```

GPS coordinates are added to the annotations similarly to the vehicle.

### Setting up the default blueprint

The default blueprint for this example is created by the following code:

```python
sensor_views = [
    dlb.Spatial2DView(
        name=sensor_name,
        origin=f"world/ego_vehicle/{sensor_name}",
        # Set the image plane distance to 5m for all camera visualizations.
        defaults=[dl.Pinhole.from_fields(image_plane_distance=5.0)],
        overrides={"world/anns": dl.Boxes3D(fill_mode="solid")},
    )
    for sensor_name in nuscene_sensor_names(nusc, args.scene_name)
]
blueprint = dlb.Vertical(
    dlb.Horizontal(
        dlb.Spatial3DView(name="3D", origin="world"),
        dlb.Vertical(
            dlb.TextDocumentView(origin="description", name="Description"),
            dlb.MapView(
                origin="world",
                name="MapView",
                zoom=dlb.archetypes.MapZoom(18.0),
                background=dlb.archetypes.MapBackground(dlb.components.MapProvider.OpenStreetMap),
            ),
            row_shares=[1, 1],
        ),
        column_shares=[3, 1],
    ),
    dlb.Grid(*sensor_views),
    row_shares=[4, 2],
)
```

We programmatically create one view per sensor and arrange them in a grid layout, which is convenient when the number of views can significantly vary from dataset to dataset. This code also showcases the `row_shares` argument for vertical containers: it can be used to assign a relative size to each of the container's children. A similar `column_shares` argument exists for horizontal containers, while grid containers accept both.




## Run the code
To run this example, make sure you have the [required Python version](https://ref.dalaran.dev/docs/python/main/common#supported-python-versions), the Dalaran repository checked out and the latest SDK installed:
```bash
pip install --upgrade dalaran-sdk  # install the latest Dalaran SDK
git clone git@github.com:Flaminis/Dalaran.git  # Clone the repository
cd dalaran
git checkout latest  # Check out the commit matching the latest SDK release
```
Install the necessary libraries specified in the requirements file:
```bash
pip install -e examples/python/nuscenes_dataset
```
To experiment with the provided example, simply execute the main Python script:
```bash
python -m nuscenes_dataset # run the example
```
If you wish to customize it, explore additional features, or save it use the CLI with the `--help` option for guidance:
```bash
python -m nuscenes_dataset --help
```
