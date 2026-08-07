"""Logs a very complex/long Annotation context for the purpose of testing/debugging the related Selection Panel UI."""

from __future__ import annotations

import argparse

import dalaran as dl
from dalaran.datatypes import ClassDescription

parser = argparse.ArgumentParser()
dl.script_add_args(parser)
args = parser.parse_args()
dl.script_setup(args, "dalaran_example_annotation_context_ui_stress")


annotation_context = dl.AnnotationContext([
    ClassDescription(
        info=(0, "class_info", (255, 0, 0)),
        keypoint_annotations=[(i, f"keypoint {i}", (255, 255 - i, 0)) for i in range(100)],
        keypoint_connections=[(i, 99 - i) for i in range(50)],
    ),
    ClassDescription(
        info=(1, "another_class_info", (255, 0, 255)),
        keypoint_annotations=[(i, f"keypoint {i}", (255, 255, i)) for i in range(100)],
        keypoint_connections=[(0, 2), (1, 2), (2, 3)],
    ),
])

# log two of those to test multi-selection
dl.log("annotation1", annotation_context)
dl.log("annotation2", annotation_context)
