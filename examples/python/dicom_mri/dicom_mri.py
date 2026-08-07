#!/usr/bin/env python3
"""Example using MRI scan data in the DICOM format."""

from __future__ import annotations

import argparse
import io
import os
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Final

import dicom_numpy
import numpy as np
import numpy.typing as npt
import pydicom as dicom
import requests

import dalaran as dl  # pip install dalaran-sdk

if TYPE_CHECKING:
    from collections.abc import Iterable

DESCRIPTION = """
# Dicom MRI
This example visualizes an MRI scan using Dalaran.

The visualization of the data consists of just the following line
```python
dl.log("tensor", dl.Tensor(voxels_volume_u16, dim_names=["right", "back", "up"]))
```

The full source code for this example is available
[on GitHub](https://github.com/Flaminis/Dalaran/blob/latest/examples/python/dicom_mri).
"""

DATASET_DIR: Final = Path(os.path.dirname(__file__)) / "dataset"
DATASET_URL: Final = "https://storage.googleapis.com/rerun-example-datasets/dicom.zip"


def extract_voxel_data(
    dicom_files: Iterable[Path],
) -> tuple[npt.NDArray[np.int16], npt.NDArray[np.float32]]:
    slices = [dicom.read_file(f) for f in dicom_files]  # type: ignore[misc]
    voxel_ndarray, ijk_to_xyz = dicom_numpy.combine_slices(slices)

    return voxel_ndarray, ijk_to_xyz


def list_dicom_files(dir: Path) -> Iterable[Path]:
    for path, _, files in os.walk(dir):
        for f in files:
            if f.endswith(".dcm"):
                yield Path(path) / f


def read_and_log_dicom_dataset(dicom_files: Iterable[Path]) -> None:
    dl.log("description", dl.TextDocument(DESCRIPTION, media_type=dl.MediaType.MARKDOWN), static=True)

    voxels_volume, _ = extract_voxel_data(dicom_files)

    # the data is i16, but in range [0, 536].
    voxels_volume_u16: npt.NDArray[np.uint16] = np.require(voxels_volume, np.uint16)

    dl.log("tensor", dl.Tensor(voxels_volume_u16, dim_names=["right", "back", "up"]))


def ensure_dataset_downloaded() -> Iterable[Path]:
    dicom_files = list(list_dicom_files(DATASET_DIR))
    if dicom_files:
        return dicom_files
    print("downloading dataset…")
    os.makedirs(DATASET_DIR.absolute(), exist_ok=True)
    resp = requests.get(DATASET_URL, stream=True)
    z = zipfile.ZipFile(io.BytesIO(resp.content))
    z.extractall(DATASET_DIR.absolute())

    return list_dicom_files(DATASET_DIR)


def main() -> None:
    parser = argparse.ArgumentParser(description="Example using MRI scan data in the DICOM format.")
    dl.script_add_args(parser)
    args = parser.parse_args()
    dl.script_setup(args, "dalaran_example_dicom_mri")
    dicom_files = ensure_dataset_downloaded()
    read_and_log_dicom_dataset(dicom_files)
    dl.script_teardown(args)


if __name__ == "__main__":
    main()
