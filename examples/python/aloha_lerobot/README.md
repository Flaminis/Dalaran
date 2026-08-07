<!--[metadata]
title = "ALOHA bimanual manipulation (LeRobot)"
tags = ["Robotics", "Manipulation", "URDF", "Time series", "Video"]
description = "Log a real ALOHA teleoperation episode from the LeRobot hub: 14 joints across two arms, an overhead camera, and commanded-vs-measured tracking."
thumbnail_dimensions = [480, 300]
-->

Logs one episode of [`lerobot/aloha_sim_transfer_cube_human`](https://huggingface.co/datasets/lerobot/aloha_sim_transfer_cube_human)
into Dalaran: a bimanual [ALOHA](https://tonyzhaozh.github.io/aloha/) robot
transferring a cube between its two arms, recorded at 50 Hz.

It is a compact tour of the robotics API:

* [`dalaran.robot.Robot`](https://dalaran.dev/docs/howto/robotics/robot-api) is
  pointed at a URDF, so `log_joint_states()` animates the real link tree — joint
  axes, limits and the mirrored `<mimic>` gripper finger are honoured for you.
* The 14 real joint trajectories are logged twice, **measured** against
  **commanded**, which is what you actually stare at when a policy or a
  teleoperator is misbehaving.
* The overhead camera is logged as a video asset and indexed on the same timeline
  as the robot, so scrubbing moves the arms and the footage together.

## Run it

```sh
pip install dalaran-sdk pyarrow numpy
python aloha_lerobot.py
```

The dataset (about 65 MB) is downloaded into `dataset/` on first run. Use
`--episode N` to pick a different episode, or `--save out.dlr` to write a
recording instead of spawning the viewer:

```sh
python aloha_lerobot.py --episode 3 --save episode3.dlr
dalaran episode3.dlr
```

## A note on the geometry

The dataset ships joint states, not a robot model, so the URDF in this example is
an approximation of a ViperX-style arm: the tube lengths and the boxes are ours,
while every joint angle, gripper position and camera frame is the robot's. If you
have the real ALOHA URDF, pass it with `Robot(urdf="path/to/aloha.urdf")` and the
same joint names will drive it, because `log_joint_states()` matches on name.
