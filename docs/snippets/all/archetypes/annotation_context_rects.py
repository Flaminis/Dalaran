import dalaran as dl

dl.init("dalaran_example_annotation_context_rects", spawn=True)

# Log an annotation context to assign a label and color to each class
dl.log(
    "/",
    dl.AnnotationContext([(1, "red", (255, 0, 0)), (2, "green", (0, 255, 0))]),
    static=True,
)

# Log a batch of 2 rectangles with different `class_ids`
dl.log(
    "detections",
    dl.Boxes2D(
        mins=[[-2, -2], [0, 0]], sizes=[[3, 3], [2, 2]], class_ids=[1, 2]
    ),
)
