import dalaran as dl

dl.set_log_tick_enabled(True)  # opt in to `log_tick` on the active recording
dl.set_log_time_enabled(False)  # opt out of `log_time` on the active recording

rec = dl.RecordingStream("dalaran_example_my_app")
rec.set_log_tick_enabled(True)  # …or on a specific recording
