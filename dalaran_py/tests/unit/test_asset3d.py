from __future__ import annotations

import pathlib

import dalaran as dl
import numpy as np

CUBE_FILEPATH = pathlib.Path(__file__).parent.parent.parent.parent / "tests" / "assets" / "mesh" / "cube.glb"
assert CUBE_FILEPATH.is_file()


def test_asset3d() -> None:
    blob_bytes = CUBE_FILEPATH.read_bytes()
    blob_comp = dl.components.Blob(blob_bytes)

    dl.set_strict_mode(True)

    assets = [
        dl.Asset3D(path=CUBE_FILEPATH),
        dl.Asset3D(path=str(CUBE_FILEPATH)),
        dl.Asset3D(contents=blob_bytes, media_type=dl.components.MediaType.GLB),
        dl.Asset3D(contents=np.frombuffer(blob_bytes, dtype=np.uint8), media_type=dl.components.MediaType.GLB),
        dl.Asset3D(contents=blob_comp, media_type=dl.components.MediaType.GLB),
    ]

    for asset in assets:
        assert asset.blob is not None
        assert asset.blob.as_arrow_array() == dl.components.BlobBatch(blob_comp).as_arrow_array()
        assert asset.media_type == dl.components.MediaTypeBatch(dl.components.MediaType.GLB)
