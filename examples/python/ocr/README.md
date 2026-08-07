<!--[metadata]
title = "PaddleOCR"
description = "Run PaddleOCR layout analysis and text detection on documents: regions, detected text, and recovered output in one view."
tags = ["Text", "OCR", "2D", "Blueprint"]
thumbnail = "https://static.rerun.io/ocr1/54b3a9d0706fd4a3a3dcbf878046ae34a7a6feec/480w.png"
thumbnail_dimensions = [480, 259]
# Channel = "main" # uncomment if this example can be run fast an easily
-->

This example visualizes layout analysis and text detection of documents using PaddleOCR.

<picture>
  <img src="https://static.rerun.io/ocr1/54b3a9d0706fd4a3a3dcbf878046ae34a7a6feec/full.png" alt="">
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/ocr1/54b3a9d0706fd4a3a3dcbf878046ae34a7a6feec/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/ocr1/54b3a9d0706fd4a3a3dcbf878046ae34a7a6feec/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/ocr1/54b3a9d0706fd4a3a3dcbf878046ae34a7a6feec/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/ocr1/54b3a9d0706fd4a3a3dcbf878046ae34a7a6feec/1200w.png">
</picture>

## Used Dalaran types

[`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image), [`TextDocument`](https://dalaran.dev/docs/reference/types/archetypes/text_document), [`Boxes2D`](https://dalaran.dev/docs/reference/types/archetypes/boxes2d), [`AnnotationContext`](https://dalaran.dev/docs/reference/types/archetypes/annotation_context)

## Background

This example demonstrates the ability to visualize and verify the document layout analysis and text detection using the [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR).
[PP-Structure](https://github.com/PaddlePaddle/PaddleOCR/tree/main/ppstructure) used for this task, which is an intelligent document analysis system developed by the PaddleOCR team, which aims to help developers better complete tasks related to document understanding such as layout analysis and table recognition.
In the layout analysis task, the image first goes through the layout analysis model to divide the image into different areas such as text, table, figure and more, and then analyze these areas separately.
The classification of layouts and the text detection (including confidence levels) are visualized in the Dalaran viewer.
Finally, the recovery text document section presents the restored document with sorted order. By clicking on the restored text, the text area will be highlighted.

## Logging and visualizing with Dalaran

The visualizations in this example were created with the following Dalaran code.

### Image

The input document is logged as [`Image`](https://www.dalaran.dev/docs/reference/types/archetypes/image) object to the `{page_path}/Image` entity.

```python
    dl.log(f"{page_path}/Image", dl.Image(image_rgb))
```

### Label mapping

An annotation context is logged with a class ID and a color assigned per layout type using [`AnnotationContext`](https://dalaran.dev/docs/reference/types/archetypes/annotation_context).

```python
class LayoutType(Enum):
    UNKNOWN = (0, "unknown", Color.Purple)
    TITLE = (1, "title", Color.Red)
    TEXT = (2, "text", Color.Green)
    FIGURE = (3, "figure", Color.Blue)
    FIGURE_CAPTION = (4, "figure_caption", Color.Yellow)
    TABLE = (5, "table", Color.Cyan)
    TABLE_CAPTION = (6, "table_caption", Color.Magenta)
    REFERENCE = (7, "reference", Color.Purple)
    FOOTER = (8, "footer", Color.Orange)

    @property
    def number(self):
        return self.value[0]  # Returns the numerical identifier

    @property
    def type(self):
        return self.value[1]  # Returns the type

    @property
    def color(self):
        return self.value[2]  # Returns the color

    @classmethod
    def get_annotation(cls):
        return [(layout.number, layout.type, layout.color) for layout in cls]


def detect_and_log_layout(img_path):
    dl.log(
        f"{page_path}/Image",
        # The annotation is defined in the Layout class based on its properties
        dl.AnnotationContext(LayoutType.get_annotation()),
        static=True,
    )
```

### Detections

The detections include the layout types and the text detections. Both of them are logged as [`Boxes2D`](https://www.dalaran.dev/docs/reference/types/archetypes/boxes2d) to Dalaran.

```python
dl.log(
    base_path,
    dl.Boxes2D(
        array=record["bounding_box"],
        array_format=dl.Box2DFormat.XYXY,
        labels=[str(layout_type.type)],
        class_ids=[str(layout_type.number)],
    ),
    dl.AnyValues(name=record_name),
)
```

Additionally, in the detection of the text, the detection id and the confidence are specified.

```python
dl.log(
    f"{base_path}/Detections/{detection['id']}",
    dl.Boxes2D(array=detection["box"], array_format=dl.Box2DFormat.XYXY, class_ids=[str(layout_type.number)]),
    dl.AnyValues(DetectionID=detection["id"], Text=detection["text"], Confidence=detection["confidence"]),
)
```

### Setting up the blueprint

[Blueprint](https://dalaran.dev/docs/concepts/visualization/blueprints) sets up the Dalaran Viewer's layout. In this example, we set the layout for the layout classification, the Detections for the text detection and the Recovery for the restored detections, which includes both layout analysis and text detections.
We dynamically set the tabs, as there will be different tabs for figures, tables and text detection.

The blueprint for this example is created by the following code:

```python
page_tabs.append(
    dlb.Vertical(
        dlb.Horizontal(
            dlb.Spatial2DView(
                name="Layout",
                origin=f"{page_path}/Image/",
                contents=[f"{page_path}/Image/**"] + detections_paths,
            ),
            dlb.Spatial2DView(name="Detections", contents=[f"{page_path}/Image/**"]),
            dlb.TextDocumentView(name="Recovery", contents=f"{page_path}/Recovery"),
        ),
        dlb.Horizontal(*section_tabs),
        name=page_path,
        row_shares=[4, 3],
    )
)

# …

dl.send_blueprint(
    dlb.Blueprint(
        dlb.Tabs(*page_tabs),
        collapse_panels=True,
    )
)
```

## Run the code

You can view this example live on [Huggingface spaces](https://huggingface.co/spaces/dalaran/OCR).\
To run this example locally, make sure you have the Dalaran repository checked out and the latest SDK installed:

```bash
pip install --upgrade dalaran-sdk  # install the latest Dalaran SDK
git clone git@github.com:rerun-io/rerun.git  # Clone the repository
cd dalaran
```

Install the necessary libraries specified in the requirements file:

```bash
pip install -e examples/python/ocr
```

To experiment with the provided example, simply execute the main Python script:

```bash
python -m ocr  # run the example
```

If you wish to customize it, explore additional features, or save it use the CLI with the `--help` option for guidance:

```bash
python -m ocr --help
```

Depending on your system, pip may grab suboptimal packages, causing slow runtimes.
Installing with [Pixi](https://pixi.sh/) has been observed to run significantly faster in this case and it will automatically install `poppler` which is required to run the example on PDF files.
To do so, simply run these commands after checking out the repository and installing Pixi:

```bash
pixi run py-build && pixi run uv run examples/python/ocr/ocr.py
```
