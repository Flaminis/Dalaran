<!--[metadata]
title = "Eigen and OpenCV C++ integration"
description = "Minimal CMake project combining Dalaran with Eigen for point and pose math and OpenCV for image reading and conversion."
source = "https://github.com/rerun-io/cpp-example-opencv-eigen"
tags = ["2D", "3D", "C++", "Eigen", "OpenCV"]
thumbnail = "https://static.rerun.io/eigen-and-opencv-c-integration/5d271725bb9215b55f53767c9dc0db980c73dade/480w.png"
thumbnail_dimensions = [480, 480]
-->



<picture>
  <img src="https://static.rerun.io/cpp-example-opencv-eigen/2fc6355fd87fbb4d07cda384ee8805edb68b5e01/full.png" alt="">
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/cpp-example-opencv-eigen/2fc6355fd87fbb4d07cda384ee8805edb68b5e01/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/cpp-example-opencv-eigen/2fc6355fd87fbb4d07cda384ee8805edb68b5e01/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/cpp-example-opencv-eigen/2fc6355fd87fbb4d07cda384ee8805edb68b5e01/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/cpp-example-opencv-eigen/2fc6355fd87fbb4d07cda384ee8805edb68b5e01/1200w.png">
</picture>

This is a minimal CMake project that shows how to use Dalaran in your code in conjunction with [Eigen](https://gitlab.com/libeigen/eigen) and [OpenCV](https://opencv.org/).


# Used Dalaran types
[`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image), [`Points3D`](https://www.dalaran.dev/docs/reference/types/archetypes/points3d), [`Pinhole`](https://www.dalaran.dev/docs/reference/types/archetypes/pinhole), [`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d)

# Background
This C++ example demonstrates the integration of the Dalaran with Eigen and OpenCV libraries.
Eigen handles 3D point calculations and camera orientations, while OpenCV assists with image processing tasks like reading and converting images.

# Logging and visualizing with Dalaran

The visualizations in this example were created with the following Dalaran code:


## 3D points
The positions of 3D points are logged to the "world/points_from_vector" and "world/points_from_matrix" entities using the [`Points3D`](https://www.dalaran.dev/docs/reference/types/archetypes/points3d) archetype.
```cpp
rec.log("world/points_from_vector", dalaran::Points3D(points3d_vector));
```

```cpp
rec.log("world/points_from_matrix", dalaran::Points3D(points3d_matrix));
```

## Pinhole camera
A pinhole camera is logged to "world/camera" using the [`Pinhole`](https://www.dalaran.dev/docs/reference/types/archetypes/pinhole) archetype.
Additionally, the 3D transformation of the camera, including its position and orientation, is logged using the [`Transform3D`](https://www.dalaran.dev/docs/reference/types/archetypes/transform3d) archetype.
```cpp
rec.log(
    "world/camera",
    dalaran::Pinhole::from_focal_length_and_resolution({500.0, 500.0}, {640.0, 480.0})
);
```

```cpp
rec.log(
    "world/camera",
    dalaran::Transform3D(
        dalaran::Vec3D(camera_position.data()),
        dalaran::Mat3x3(camera_orientation.data())
    )
);
```

## Images
Images are logged using the [`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image) archetype. Two methods are demonstrated: logging images with a tensor buffer and logging images by passing a pointer to the image data.
```cpp
// Log image to dalaran by borrowing binary data into a `Collection` from a pointer.
rec.log(
    "image0",
    dalaran::Image(
        dalaran::borrow(img.data, img.total() * img.elemSize()),
        dalaran::WidthHeight(
            static_cast<uint32_t>(img.cols),
            static_cast<uint32_t>(img.rows)
        ),
        dalaran::ColorModel::BGR
    )
);

// Or by passing a pointer to the image data.
rec.log(
    "image1",
    dalaran::Image(
        reinterpret_cast<const uint8_t*>(img.data),
        dalaran::WidthHeight(
            static_cast<uint32_t>(img.cols),
            static_cast<uint32_t>(img.rows)
        ),
        dalaran::ColorModel::BGR
    )
);
```

# Run the code
You can find the build instructions here: [C++ Example with OpenCV and Eigen](https://github.com/rerun-io/cpp-example-opencv-eigen/blob/main/README.md)
