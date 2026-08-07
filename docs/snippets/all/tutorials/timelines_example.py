for frame in read_sensor_frames():
    dl.set_time("frame_idx", sequence=frame.idx)
    dl.set_time("sensor_time", timestamp=frame.timestamp)

    dl.log("sensor/points", dl.Points3D(frame.points))
