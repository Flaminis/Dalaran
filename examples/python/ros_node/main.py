#!/usr/bin/env python3
"""
Simple example of a ROS node that republishes some common types to Dalaran.

The solution here is mostly a toy example to show how ROS concepts can be
mapped to Dalaran. For more information on future improved ROS support,
see the tracking issue: <https://github.com/rerun-io/rerun/issues/1537>.

NOTE: Unlike many of the other examples, this example requires a system installation of ROS
in addition to the packages from requirements.txt.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

import numpy as np

import dalaran as dl  # pip install dalaran-sdk
from dalaran.components import Colormap

try:
    import cv_bridge
    import laser_geometry
    import rclpy
    from image_geometry import PinholeCameraModel
    from nav_msgs.msg import OccupancyGrid, Odometry
    from numpy.lib.recfunctions import structured_to_unstructured
    from rclpy.callback_groups import ReentrantCallbackGroup
    from rclpy.node import Node
    from rclpy.qos import QoSDurabilityPolicy, QoSProfile
    from rclpy.time import Time
    from sensor_msgs.msg import CameraInfo, Image, LaserScan
    from sensor_msgs_py import point_cloud2
    from std_msgs.msg import String
    from tf2_msgs.msg import TFMessage

except ImportError:
    print(
        """
Could not import the required ROS2 packages.

Make sure you have installed ROS2 (https://docs.ros.org/en/kilted/index.html)
and sourced /opt/ros/kilted/setup.bash

See: README.md for more details.
""",
    )
    sys.exit(1)


class TurtleSubscriber(Node):  # type: ignore[misc]
    def __init__(self) -> None:
        super().__init__("rr_turtlebot")

        # Assorted helpers for data conversions
        self.pinhole_model = PinholeCameraModel()
        self.cv_bridge = cv_bridge.CvBridge()
        self.laser_proj = laser_geometry.laser_geometry.LaserProjection()
        self.subscribers: list[rclpy.Subscription] = []

        # Subscribe to the topics we want to republish to Dalaran.
        # See the callback methods below for how each message type is handled.
        self.subscribe("/tf", TFMessage, self.tf_callback)
        self.subscribe("/tf_static", TFMessage, self.tf_callback, latching=True)
        self.subscribe("/odom", Odometry, self.odom_callback)
        self.subscribe("/scan", LaserScan, self.scan_callback)
        self.subscribe("/rgbd_camera/camera_info", CameraInfo, self.cam_info_callback)
        self.subscribe("/rgbd_camera/image", Image, self.image_callback)
        self.subscribe("/rgbd_camera/depth_image", Image, self.depth_callback)
        self.subscribe("/robot_description", String, self.urdf_callback, latching=True)
        self.subscribe(
            "/map",
            OccupancyGrid,
            lambda grid: self.occupancy_grid_callback("/map", grid, Colormap.RvizMap, draw_order=1.0),
            latching=True,
        )
        self.subscribe(
            "/global_costmap/costmap",
            OccupancyGrid,
            lambda grid: self.occupancy_grid_callback(
                "/global_costmap_costmap", grid, Colormap.RvizCostmap, draw_order=2.0, opacity=0.75
            ),
        )
        self.subscribe(
            "/local_costmap/costmap",
            OccupancyGrid,
            lambda grid: self.occupancy_grid_callback(
                "/local_costmap_costmap", grid, Colormap.RvizCostmap, draw_order=3.0, opacity=0.75
            ),
        )

    def subscribe(
        self, topic: str, msg_type: type, callback: Callable[[rclpy.MsgT], None], latching: bool = False
    ) -> None:
        """Adds a subscriber to a topic with the given message type and callback."""
        # `qos_profile` can either be an int (history depth) or a QoSProfile.
        # See: https://docs.ros.org/en/rolling/p/rclpy/rclpy.node.html#rclpy.node.Node.create_subscription
        qos_profile = QoSProfile(depth=1, durability=QoSDurabilityPolicy.TRANSIENT_LOCAL) if latching else 10
        sub = self.create_subscription(
            msg_type=msg_type,
            topic=topic,
            callback=callback,
            qos_profile=qos_profile,
            callback_group=ReentrantCallbackGroup(),  # allow concurrent callbacks
        )
        self.subscribers.append(sub)

    def cam_info_callback(self, info: CameraInfo) -> None:
        """
        Logs CameraInfo as a Dalaran Pinhole.
        """
        time = Time.from_msg(info.header.stamp)
        self.pinhole_model.from_camera_info(info)
        dl.set_time("ros_time", timestamp=np.datetime64(time.nanoseconds, "ns"))
        dl.log(
            "rgbd_camera/camera_info",
            dl.Pinhole(
                resolution=[info.width, info.height],
                image_from_camera=self.pinhole_model.intrinsic_matrix(),
                image_plane_distance=1.0,
                parent_frame=info.header.frame_id,
                # Specifying a `child_frame` for the 2D image plane allows Dalaran to
                # visualize the pinhole frustum together with the image in 3D views.
                # This has to match the coordinate frames used when logging images,
                # see `image_callback` below.
                child_frame=info.header.frame_id + "_image_plane",
            ),
        )

    def odom_callback(self, odom: Odometry) -> None:
        """
        Logs data from Odometry as Dalaran Scalars.
        """
        time = Time.from_msg(odom.header.stamp)
        dl.set_time("ros_time", timestamp=np.datetime64(time.nanoseconds, "ns"))
        # Capture time-series data for the linear and angular velocities
        dl.log("odom/twist/linear/x", dl.Scalars(odom.twist.twist.linear.x))
        dl.log("odom/twist/angular/z", dl.Scalars(odom.twist.twist.angular.z))

    def image_callback(self, img: Image) -> None:
        """
        Logs an RGB image as a Dalaran Image.
        """
        time = Time.from_msg(img.header.stamp)
        dl.set_time("ros_time", timestamp=np.datetime64(time.nanoseconds, "ns"))
        dl.log("rgbd_camera/image", dl.Image(self.cv_bridge.imgmsg_to_cv2(img)))
        # Make sure the image plane frame matches what we set in `cam_info_callback`.
        dl.log("rgbd_camera/image", dl.CoordinateFrame(frame=img.header.frame_id + "_image_plane"))

    def depth_callback(self, img: Image) -> None:
        """
        Logs a depth image as a Dalaran DepthImage.
        """
        time = Time.from_msg(img.header.stamp)
        depth_image = dl.DepthImage(
            self.cv_bridge.imgmsg_to_cv2(img, desired_encoding="32FC1"),
            meter=1.0,
            colormap="viridis",
        )
        dl.set_time("ros_time", timestamp=np.datetime64(time.nanoseconds, "ns"))
        dl.log("rgbd_camera/depth_image", depth_image)
        dl.log("rgbd_camera/depth_image", dl.CoordinateFrame(frame=img.header.frame_id + "_image_plane"))

    def occupancy_grid_callback(
        self,
        entity_path: str,
        grid: OccupancyGrid,
        colormap: dl.components.Colormap,
        draw_order: float | None = None,
        opacity: float | None = None,
    ) -> None:
        """
        Logs a ROS OccupancyGrid as a Dalaran GridMap.
        """
        time = Time.from_msg(grid.header.stamp)
        dl.set_time("ros_time", timestamp=np.datetime64(time.nanoseconds, "ns"))

        # Log the coordinate frame ID of the map.
        # The local offset of the map frame within the grid is handled by the archetype (see below).
        dl.log(entity_path, dl.CoordinateFrame(frame=grid.header.frame_id))

        # ROS maps start at the bottom-left cell; Dalaran image buffers are top-row first.
        data = np.asarray(grid.data, dtype=np.int8).reshape((grid.info.height, grid.info.width))
        image_data = np.flipud(data).astype(np.uint8, copy=False)

        dl.log(
            entity_path,
            dl.GridMap(
                data=image_data.tobytes(),
                format=dl.components.ImageFormat(
                    width=grid.info.width,
                    height=grid.info.height,
                    color_model="L",
                    channel_datatype="U8",
                ),
                cell_size=grid.info.resolution,
                translation=[
                    grid.info.origin.position.x,
                    grid.info.origin.position.y,
                    grid.info.origin.position.z,
                ],
                quaternion=dl.Quaternion(
                    xyzw=[
                        grid.info.origin.orientation.x,
                        grid.info.origin.orientation.y,
                        grid.info.origin.orientation.z,
                        grid.info.origin.orientation.w,
                    ]
                ),
                colormap=colormap,
                draw_order=draw_order,
                opacity=opacity,
            ),
        )

    def scan_callback(self, scan: LaserScan) -> None:
        """
        Logs a LaserScan after transforming it to line-segments.

        Note: we do a client-side transformation of the LaserScan data into Dalaran
        points / lines until Dalaran has native support for LaserScan style projections:
        [#1534](https://github.com/rerun-io/rerun/issues/1534)
        """
        time = Time.from_msg(scan.header.stamp)
        dl.set_time("ros_time", timestamp=np.datetime64(time.nanoseconds, "ns"))

        # Project the laser scan to a collection of points
        points = self.laser_proj.projectLaser(scan)
        pts = point_cloud2.read_points(points, field_names=["x", "y", "z"], skip_nans=True)
        pts = structured_to_unstructured(pts)

        # Turn every pt into a line-segment from the origin to the point.
        origin = (pts / np.linalg.norm(pts, axis=1).reshape(-1, 1)) * 0.3
        segs = np.hstack([origin, pts]).reshape(pts.shape[0] * 2, 3)

        dl.log("scan", dl.LineStrips3D(segs, radii=0.0025, colors=[255, 165, 0]))
        dl.log("scan", dl.CoordinateFrame(frame=scan.header.frame_id))

    def urdf_callback(self, urdf_msg: String) -> None:
        """
        Forwards the robot description message to Dalaran's built-in URDF loader.

        Documentation about URDF support in Dalaran can be found here:
        https://dalaran.dev/docs/howto/logging-and-ingestion/urdf
        """
        # NOTE: file_path is not known here, robot.urdf is just a placeholder to let
        # Dalaran know the file type. Since we run this example in a ROS environment,
        # Dalaran can use AMENT_PREFIX_PATH etc to resolve asset paths of the URDF.
        dl.log_file_from_contents(
            file_path="robot.urdf",
            file_contents=urdf_msg.data.encode("utf-8"),
            entity_path_prefix="urdf",
            static=True,
        )

    def tf_callback(self, tf_msg: TFMessage) -> None:
        """
        Logs TF transforms to Dalaran as Transform3D messages,
        with `parent_frame` and `child_frame` fields set.

        Documentation about transforms in Dalaran can be found here:
        https://dalaran.dev/docs/concepts/transforms
        """
        for transform in tf_msg.transforms:
            time = Time.from_msg(transform.header.stamp)
            dl.set_time("ros_time", timestamp=np.datetime64(time.nanoseconds, "ns"))
            dl.log(
                "transforms",
                dl.Transform3D(
                    translation=[
                        transform.transform.translation.x,
                        transform.transform.translation.y,
                        transform.transform.translation.z,
                    ],
                    rotation=dl.Quaternion(
                        xyzw=[
                            transform.transform.rotation.x,
                            transform.transform.rotation.y,
                            transform.transform.rotation.z,
                            transform.transform.rotation.w,
                        ]
                    ),
                    parent_frame=transform.header.frame_id,
                    child_frame=transform.child_frame_id,
                ),
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple example of a ROS node that republishes to Dalaran.")
    dl.script_add_args(parser)
    args, unknownargs = parser.parse_known_args()
    dl.script_setup(args, "dalaran_example_ros_node")

    # Any remaining args go to rclpy
    rclpy.init(args=unknownargs)

    turtle_subscriber = TurtleSubscriber()

    # Use the MultiThreadedExecutor so that calls to `lookup_transform` don't block the other threads
    rclpy.spin(turtle_subscriber, executor=rclpy.executors.MultiThreadedExecutor())

    turtle_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
