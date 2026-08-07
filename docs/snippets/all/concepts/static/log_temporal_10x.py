dl.set_time("frame", sequence=4)
for _ in range(10):
    dl.log("camera/image", camera.save_current_frame())
