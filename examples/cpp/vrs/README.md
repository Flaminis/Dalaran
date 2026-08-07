<!--[metadata]
title = "VRS viewer"
description = "A C++ example that loads VRS (Facebook's per-device sensor record format) into Dalaran: images, audio, IMU, and more."
source = "https://github.com/rerun-io/cpp-example-vrs"
tags = ["2D", "3D", "VRS", "Viewer", "C++"]
thumbnail = "https://static.rerun.io/vrs/614f0adf0dd31fa01fff0d6eaeae67bbe8ba9af0/480w.png"
thumbnail_dimensions = [480, 482]
-->

<picture>
  <img src="https://static.rerun.io/cpp-example-vrs/c765460d4448da27bb9ee2a2a15f092f82a402d2/full.png" alt="">
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/cpp-example-vrs/c765460d4448da27bb9ee2a2a15f092f82a402d2/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/cpp-example-vrs/c765460d4448da27bb9ee2a2a15f092f82a402d2/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/cpp-example-vrs/c765460d4448da27bb9ee2a2a15f092f82a402d2/1024w.png">
</picture>

This is an example that shows how to use Dalaran's C++ API to log and view [VRS](https://github.com/facebookresearch/vrs) files.


# Used Dalaran types

[`Arrows3D`](https://www.dalaran.dev/docs/reference/types/archetypes/arrows3d), [`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image), [`Scalars`](https://www.dalaran.dev/docs/reference/types/archetypes/scalars), [`TextDocument`](https://www.dalaran.dev/docs/reference/types/archetypes/text_document)

# Background
This C++ example demonstrates how to visualize VRS files with Dalaran.
VRS is a file format optimized to record & playback streams of sensor data, such as images, audio samples, and any other discrete sensors (IMU, temperature, etc), stored in per-device streams of time-stamped records.

# Logging and visualizing with Dalaran

The visualizations in this example were created with the following Dalaran code:

## 3D arrows
```cpp
void IMUPlayer::log_accelerometer(const std::array<float, 3>& accelMSec2) {
    _rec->log(_entity_path + "/accelerometer", dalaran::Arrows3D::from_vectors({accelMSec2}));
    // … existing code for scalars …
}
```

## Scalars
```cpp
void IMUPlayer::log_accelerometer(const std::array<float, 3>& accelMSec2) {
    // … existing code for Arrows3D …
    _rec->log(_entity_path + "/accelerometer", dalaran::Scalars(accelMSec2));
}
```

```cpp
void IMUPlayer::log_gyroscope(const std::array<float, 3>& gyroRadSec) {
    _rec->log(_entity_path + "/gyroscope", dalaran::Scalars(gyroRadSec));
}
```

```cpp
void IMUPlayer::log_magnetometer(const std::array<float, 3>& magTesla) {
    _rec->log(_entity_path + "/magnetometer", dalaran::Scalars(magTesla));
}
```

## Images
```cpp
_rec->log(
    _entity_path,
    dalaran::Image({
    frame->getHeight(),
    frame->getWidth(),
    frame->getSpec().getChannelCountPerPixel()},
    frame->getBuffer()
    )
);
```

## Text document
```cpp
_rec->log_static(_entity_path + "/configuration", dalaran::TextDocument(layout_str));
```

# Run the code
You can find the build instructions here: [C++ Example: VRS Viewer](https://github.com/rerun-io/cpp-example-vrs)
