<!--[metadata]
title = "SO-100 pick and place"
tags = ["Robotics", "Manipulation", "URDF", "Video", "Time series"]
description = "Drive the real SO-ARM100 URDF with recorded joint angles from a LeRobot pick-and-place episode, next to the overhead and wrist camera footage."
thumbnail_dimensions = [480, 300]
-->

An SO-100 arm picking up a cube and placing it in a box, from
[`lerobot/svla_so100_pickplace`](https://huggingface.co/datasets/lerobot/svla_so100_pickplace).

Everything on screen is real: the 6 joint trajectories, the gripper, both camera
videos, and the robot itself — this is the
[SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) URDF with its STL meshes,
driven by the recorded joint angles. The arm in the 3D view is the arm that shot
the footage beside it.

What it shows off:

* [`dalaran.robot.Robot`](https://dalaran.dev/docs/howto/robotics/urdf) pointed at
  a URDF, so `log_joint_states()` animates the real link tree. The dataset reports
  degrees and the URDF is in radians; the example converts.
* **commanded vs measured** for every joint, which is what you actually stare at
  when a policy or a teleoperator misbehaves.
* Two cameras placed in the **frame graph**: the overhead camera is fixed to the
  robot's `base` frame, while the wrist camera hangs off the moving `gripper`
  frame, so it travels with the arm.

## Run it

The URDF and its meshes are stored with git-LFS, so fetch them once:

```sh
git lfs pull --include="examples/rust/animated_urdf/data/**"
```

Then:

```sh
pip install dalaran-sdk numpy pyarrow
python so100_pickplace.py
```

The dataset is downloaded into `dataset/` on first run (about 450 MB, mostly the
two videos). Use `--episode N` for a different episode, `--urdf` to point at your
own robot model, or `--save out.dlr` to write a recording instead of spawning the
viewer:

```sh
python so100_pickplace.py --episode 2 --save episode2.dlr
dalaran episode2.dlr
```
