from __future__ import annotations

from unittest.mock import patch

import pytest
import dalaran as dl


@pytest.mark.parametrize(
    ["archetype", "expected"],
    [
        [
            dl.Transform3D().from_fields(clear_unset=True),
            (
                "dl.Transform3D(\n"
                "  translation=[],\n"
                "  rotation_axis_angle=[],\n"
                "  quaternion=[],\n"
                "  scale=[],\n"
                "  mat3x3=[],\n"
                "  relation=[],\n"
                "  child_frame=[],\n"
                "  parent_frame=[]\n"
                ")"
            ),
        ],
        [
            dl.Transform3D(translation=[10, 10, 10]),
            ("dl.Transform3D(\n  translation=[[10.0, 10.0, 10.0]]\n)"),
        ],
        [
            dl.Points2D(positions=[[0, 0], [1, 1], [2, 2]]),
            "dl.Points2D(\n  positions=[[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]\n)",
        ],
        [
            dl.Points2D(positions=[0, 0, 1, 1, 2, 2], radii=[4, 5, 6]),
            "dl.Points2D(\n  positions=[[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]],\n  radii=[4.0, 5.0, 6.0]\n)",
        ],
        [dl.Points2D.from_fields(), "dl.Points2D()"],
        [
            dl.Points3D(
                [
                    11,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    2,
                    3,
                    3,
                ],
                radii=[1, 2, 3],
            ),
            """\
dl.Points3D(
  positions=[[11.0, 2.0, 3.0], [2.0, 3.0, 2.0], [3.0, 2.0, 3.0], [2.0, 3.0, 2.0],
    [3.0, 2.0, 3.0], [2.0, 3.0, 2.0], [3.0, 2.0, 3.0], [2.0, 3.0, 2.0],
    [3.0, 2.0, 3.0], [2.0, 3.0, 2.0], [3.0, 2.0, 3.0], [2.0, 3.0, 3.0]],
  radii=[1.0, 2.0, 3.0]
)""",
        ],
    ],
)
def test_archetype_str(archetype: dl._baseclasses.Archetype, expected: str) -> None:
    assert str(archetype) == expected


def test_archetype_str_normalization() -> None:
    """Test that archetype names are correct regardless of import path."""
    # `import dalaran`
    assert dl.Points3D.archetype() == "dalaran.archetypes.Points3D"
    assert dl.Points3D.archetype_short_name() == "Points3D"

    # `import dalaran_sdk.dalaran`
    with patch.object(dl.Points3D, "__module__", "dalaran_sdk.dalaran.archetypes.points3d"):
        assert dl.Points3D.archetype() == "dalaran.archetypes.Points3D"
        assert dl.Points3D.archetype_short_name() == "Points3D"
