<!--[metadata]
title = "Stereo vision SLAM"
description = "Stereo-vision SLAM on the KITTI self-driving dataset: vehicle trajectory plus the surrounding point cloud."
source = "https://github.com/rerun-io/StereoVision-SLAM"
tags = ["3D", "Point cloud", "C++"]
thumbnail = "https://static.rerun.io/stereovision_slam/c36cfcf8bc7ec9f03b40559d596d7fee97907ba8/480w.png"
thumbnail_dimensions = [480, 273]
-->

Visualizes stereo vision SLAM on the [KITTI dataset](https://www.cvlibs.net/datasets/kitti/).

<picture>
  <img src="https://static.rerun.io/stereovision_slam_full/675db4870c12da348552ac9bcdf4c60228d77322/full.png" alt="">
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/stereovision_slam_full/675db4870c12da348552ac9bcdf4c60228d77322/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/stereovision_slam_full/675db4870c12da348552ac9bcdf4c60228d77322/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/stereovision_slam_full/675db4870c12da348552ac9bcdf4c60228d77322/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/stereovision_slam_full/675db4870c12da348552ac9bcdf4c60228d77322/1200w.png">
</picture>

# Used Dalaran types

[`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image), [`LineStrips3D`](https://dalaran.dev/docs/reference/types/archetypes/line_strips3d), [`Scalars`](https://dalaran.dev/docs/reference/types/archetypes/scalars), [`Transform3D`](https://dalaran.dev/docs/reference/types/archetypes/transform3d), [`Pinhole`](https://dalaran.dev/docs/reference/types/archetypes/pinhole), [`Points3D`](https://dalaran.dev/docs/reference/types/archetypes/points3d), [`TextLog`](https://dalaran.dev/docs/reference/types/archetypes/text_log)


# Background

This example shows [farhad-dalirani's stereo visual SLAM implementation](https://github.com/farhad-dalirani/StereoVision-SLAM). It's input is the video footage from a stereo camera and it produces the trajectory of the vehicle and a point cloud of the surrounding environment.

# Logging and visualizing with Dalaran

To easily use Opencv/Eigen types and avoid copying images/points when logging to Dalaran it uses [`CollectionAdapter`](https://ref.dalaran.dev/docs/cpp/stable/structdalaran_1_1CollectionAdapter.html) with the following code:
```cpp

template <>
struct dalaran::CollectionAdapter<uint8_t, cv::Mat>
{
    /* Adapters to borrow an OpenCV image into Dalaran
     * images without copying */

    Collection<uint8_t> operator()(const cv::Mat& img)
    {
        // Borrow for non-temporary.

        assert("OpenCV matrix expected have bit depth CV_U8" && CV_MAT_DEPTH(img.type()) == CV_8U);
        return Collection<uint8_t>::borrow(img.data, img.total() * img.channels());
    }

    Collection<uint8_t> operator()(cv::Mat&& img)
    {
        /* Do a full copy for temporaries (otherwise the data
         * might be deleted when the temporary is destroyed). */

        assert("OpenCV matrix expected have bit depth CV_U8" && CV_MAT_DEPTH(img.type()) == CV_8U);
        std::vector<uint8_t> img_vec(img.total() * img.channels());
        img_vec.assign(img.data, img.data + img.total() * img.channels());
        return Collection<uint8_t>::take_ownership(std::move(img_vec));
    }
};


template <>
struct dalaran::CollectionAdapter<dalaran::Position3D, std::vector<Eigen::Vector3f>>
{
    /* Adapters to log eigen vectors as dalaran positions*/

    Collection<dalaran::Position3D> operator()(const std::vector<Eigen::Vector3f>& container)
    {
        // Borrow for non-temporary.
        return Collection<dalaran::Position3D>::borrow(container.data(), container.size());
    }

    Collection<dalaran::Position3D> operator()(std::vector<Eigen::Vector3f>&& container)
    {
        /* Do a full copy for temporaries (otherwise the data
         * might be deleted when the temporary is destroyed). */
        std::vector<dalaran::Position3D> positions(container.size());
        memcpy(positions.data(), container.data(), container.size() * sizeof(Eigen::Vector3f));
        return Collection<dalaran::Position3D>::take_ownership(std::move(positions));
    }
};


template <>
struct dalaran::CollectionAdapter<dalaran::Position3D, Eigen::Matrix3Xf>
{
    /* Adapters so we can log an eigen matrix as dalaran positions */

    // Sanity check that this is binary compatible.
    static_assert(
        sizeof(dalaran::Position3D) == sizeof(Eigen::Matrix3Xf::Scalar) * Eigen::Matrix3Xf::RowsAtCompileTime
    );

    Collection<dalaran::Position3D> operator()(const Eigen::Matrix3Xf& matrix)
    {
        // Borrow for non-temporary.
        static_assert(alignof(dalaran::Position3D) <= alignof(Eigen::Matrix3Xf::Scalar));
        return Collection<dalaran::Position3D>::borrow(
            // Cast to void because otherwise Dalaran will try to do above sanity checks with the wrong type (scalar).
            reinterpret_cast<const void*>(matrix.data()),
            matrix.cols()
        );
    }

    Collection<dalaran::Position3D> operator()(Eigen::Matrix3Xf&& matrix)
    {
        /* Do a full copy for temporaries (otherwise the
         * data might be deleted when the temporary is destroyed). */
        std::vector<dalaran::Position3D> positions(matrix.cols());
        memcpy(positions.data(), matrix.data(), matrix.size() * sizeof(dalaran::Position3D));
        return Collection<dalaran::Position3D>::take_ownership(std::move(positions));
    }
};

```

## Images
```cpp
// Draw stereo left image
rec.log(entity_name,
        dalaran::Image(tensor_shape(kf_sort[0].second->left_img_),
                    dalaran::TensorBuffer::u8(kf_sort[0].second->left_img_)));
```

## Pinhole camera

The camera frames shown in the view is generated by the following code:

```cpp
rec.log(entity_name,
    dalaran::Transform3D(
        dalaran::Vec3D(camera_position.data()),
        dalaran::Mat3x3(camera_orientation.data()), true)
);
// …
rec.log(entity_name,
        dalaran::Pinhole::from_focal_length_and_resolution({fx, fy}, {img_num_cols, img_num_rows}));
```

## Time series
```cpp
void Viewer::Plot(std::string plot_name, double value, unsigned long maxkeyframe_id)
{
    // …
    rec.set_time_sequence("max_keyframe_id", maxkeyframe_id);
    rec.log(plot_name, dalaran::Scalars(value));
}
```

## Trajectory
```cpp
rec.log("world/path",
    dalaran::Transform3D(
        dalaran::Vec3D(camera_position.data()),
        dalaran::Mat3x3(camera_orientation.data()), true));

std::vector<dalaran::datatypes::Vec3D> path;
// …
rec.log("world/path", dalaran::LineStrips3D(dalaran::LineStrip3D(path)));
```

## Point cloud
```cpp
rec.log("world/landmarks",
    dalaran::Transform3D(
        dalaran::Vec3D(camera_position.data()),
        dalaran::Mat3x3(camera_orientation.data()), true));

std::vector<Eigen::Vector3f> points3d_vector;
// …
rec.log("world/landmarks", dalaran::Points3D(points3d_vector));
```

## Text log

```cpp
rec.log("world/log", dalaran::TextLog(msg).with_color(log_color.at(log_type)));
// …
rec.log("world/log", dalaran::TextLog("Finished"));
```

# Run the code

This is an external example, check the [repository](https://github.com/rerun-io/StereoVision-SLAM) on how to run the code.
