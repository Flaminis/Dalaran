<!--[metadata]
title = "Detect and track objects"
description = "Object detection from Hugging Face Transformers plus OpenCV optical-flow tracking, aligned to the source video."
tags = ["2D", "Hugging face", "Object detection", "Object tracking", "OpenCV"]
thumbnail = "https://static.rerun.io/detect-and-track-objects/63d7684ab1504c86a5375cb5db0fc515af433e08/480w.png"
thumbnail_dimensions = [480, 480]
channel = "release"
include_in_manifest = true
allow_warnings = true # TODO(emilk): torch produces a warning because of `transformers` (I think?). We should fix that, if we can.
-->

Visualize object detection and segmentation using the [Huggingface's Transformers](https://huggingface.co/docs/transformers/index) and optical flow tracking from OpenCV.

<picture data-inline-viewer="examples/detect_and_track_objects">
  <img src="https://static.rerun.io/detact_and_track_objects/ce1939b8f2d22b36c4ca8b36dc0441e106b51da5/full.png" alt="">
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/detact_and_track_objects/ce1939b8f2d22b36c4ca8b36dc0441e106b51da5/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/detact_and_track_objects/ce1939b8f2d22b36c4ca8b36dc0441e106b51da5/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/detact_and_track_objects/ce1939b8f2d22b36c4ca8b36dc0441e106b51da5/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/detact_and_track_objects/ce1939b8f2d22b36c4ca8b36dc0441e106b51da5/1200w.png">
</picture>

## Used Dalaran types
[`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image), [`AssetVideo`](https://www.dalaran.dev/docs/reference/types/archetypes/asset_video), [`VideoFrameReference`](https://dalaran.dev/docs/reference/types/archetypes/video_frame_reference), [`SegmentationImage`](https://www.dalaran.dev/docs/reference/types/archetypes/segmentation_image), [`AnnotationContext`](https://www.dalaran.dev/docs/reference/types/archetypes/annotation_context), [`Boxes2D`](https://www.dalaran.dev/docs/reference/types/archetypes/boxes2d), [`TextLog`](https://www.dalaran.dev/docs/reference/types/archetypes/text_log)

## Background
In this example, optical flow tracking from OpenCV is employed for tracking objects across frames.
Additionally, the example showcases basic object detection and segmentation on a video using the Huggingface transformers library.


## Logging and visualizing with Dalaran
The visualizations in this example were created with the following Dalaran code.


### Timelines
For each processed video frame, all data sent to Dalaran is associated with the [`timelines`](https://www.dalaran.dev/docs/concepts/logging-and-ingestion/timelines) `frame_idx`.

```python
dl.set_time("frame", sequence=frame_idx)
```

### Video
The input video is logged as a static [`AssetVideo`](https://www.dalaran.dev/docs/reference/types/archetypes/asset_video) to the `video` entity.

```python
video_asset = dl.AssetVideo(path=video_path)
frame_timestamps_ns = video_asset.read_frame_timestamps_nanos()

dl.log("video", video_asset, static=True)
```

Each frame is processed and the timestamp is logged to the `frame` timeline using a [`VideoFrameReference`](https://www.dalaran.dev/docs/reference/types/archetypes/video_frame_reference).

```python
dl.log("video", dl.VideoFrameReference(nanoseconds=frame_timestamps_ns[frame_idx]))
```

Since the detection and segmentation model operates on smaller images the resized images are logged to the separate `segmentation/rgb_scaled` entity.
This allows us to subsequently visualize the segmentation mask on top of the video.

```python
dl.log("segmentation/rgb_scaled", dl.Image(rgb_scaled).compress(jpeg_quality=85))
```

### Segmentations
The segmentation results is logged through a combination of two archetypes.
The segmentation image itself is logged as an
[`SegmentationImage`](https://www.dalaran.dev/docs/reference/types/archetypes/segmentation_image) and
contains the id for each pixel. It is logged to the `segmentation` entity.


```python
dl.log("segmentation", dl.SegmentationImage(mask))
```

The color and label for each class is determined by the
[`AnnotationContext`](https://www.dalaran.dev/docs/reference/types/archetypes/annotation_context) which is
logged to the root entity using `dl.log("/", …, static=True)` as it should apply to the whole sequence and all
entities that have a class id.

```python
class_descriptions = [dl.AnnotationInfo(id=cat["id"], color=cat["color"], label=cat["name"]) for cat in coco_categories]
dl.log("/", dl.AnnotationContext(class_descriptions), static=True)
```

### Detections
The detections and tracked bounding boxes are visualized by logging the [`Boxes2D`](https://www.dalaran.dev/docs/reference/types/archetypes/boxes2d) to Dalaran.

#### Detections
```python
dl.log(
    "segmentation/detections/things",
    dl.Boxes2D(
        array=thing_boxes,
        array_format=dl.Box2DFormat.XYXY,
        class_ids=thing_class_ids,
    ),
)
```

```python
dl.log(
    f"image/tracked/{self.tracking_id}",
    dl.Boxes2D(
        array=self.tracked.bbox_xywh,
        array_format=dl.Box2DFormat.XYWH,
        class_ids=self.tracked.class_id,
    ),
)
```
#### Tracked bounding boxes
```python
dl.log(
    "segmentation/detections/background",
    dl.Boxes2D(
        array=background_boxes,
        array_format=dl.Box2DFormat.XYXY,
        class_ids=background_class_ids,
    ),
)
```

The color and label of the bounding boxes is determined by their class id, relying on the same
[`AnnotationContext`](https://www.dalaran.dev/docs/reference/types/archetypes/annotation_context) as the
segmentation images. This ensures that a bounding box and a segmentation image with the same class id will also have the
same color.

Note that it is also possible to log multiple annotation contexts should different colors and / or labels be desired.
The annotation context is resolved by seeking up the entity hierarchy.

### Text log
Dalaran integrates with the [Python logging module](https://docs.python.org/3/library/logging.html).
Through the [`TextLog`](https://www.dalaran.dev/docs/reference/types/archetypes/text_log#textlogintegration) text at different importance level can be logged. After an initial setup that is described on the
[`TextLog`](https://www.dalaran.dev/docs/reference/types/archetypes/text_log#textlogintegration), statements
such as `logging.info("…")`, `logging.debug("…")`, etc. will show up in the Dalaran viewer.

```python
def setup_logging() -> None:
    logger = logging.getLogger()
    dalaran_handler = dl.LoggingHandler("logs")
    dalaran_handler.setLevel(-1)
    logger.addHandler(dalaran_handler)


def main() -> None:
    # … existing code …
    setup_logging()  # setup logging
    track_objects(video_path, max_frame_count=args.max_frame)  # start tracking
```
In the Viewer you can adjust the filter level and look at the messages time-synchronized with respect to other logged data.

## Run the code
To run this example, make sure you have the Dalaran repository checked out and the latest SDK installed:
```bash
pip install --upgrade dalaran-sdk  # install the latest Dalaran SDK
git clone git@github.com:Flaminis/Dalaran.git  # Clone the repository
cd dalaran
git checkout latest  # Check out the commit matching the latest SDK release
```

Install the necessary libraries specified in the requirements file:
```bash
pip install -e examples/python/detect_and_track_objects
```
To experiment with the provided example, simply execute the main Python script:
```bash
python -m detect_and_track_objects # run the example
```

If you wish to customize it for various videos, adjust the maximum frames, explore additional features, or save it use the CLI with the `--help` option for guidance:

```bash
python -m detect_and_track_objects --help
```
