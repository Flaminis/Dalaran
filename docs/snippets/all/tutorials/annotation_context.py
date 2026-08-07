import dalaran as dl

dl.init("dalaran_example_annotation_context_connections")

# Annotation context with two classes, using two labeled classes, of which
# ones defines a color.
dl.log(
    "masks",  # Applies to all entities below "masks".
    dl.AnnotationContext(
        [
            dl.AnnotationInfo(id=0, label="Background"),
            dl.AnnotationInfo(id=1, label="Person", color=(255, 0, 0)),
        ],
    ),
    static=True,
)

# Annotation context with simple keypoints & keypoint connections.
dl.log(
    "detections",  # Applies to all entities below "detections".
    dl.ClassDescription(
        info=dl.AnnotationInfo(0, label="Snake"),
        keypoint_annotations=[
            dl.AnnotationInfo(id=i, color=(0, 28 * i, 0)) for i in range(10)
        ],
        keypoint_connections=[(i, i + 1) for i in range(9)],
    ),
    static=True,
)
