import dalaran as dl

# 0.8
dl.log_point("my_point", [1.0, 2.0, 3.0])  # type: ignore[attr-defined]

# 0.9
dl.log("my_point", dl.Points3D([1.0, 2.0, 3.0]))
