#!/usr/bin/env python3
"""Regenerate static blueprint resources for E2E redap tests."""

from __future__ import annotations

from pathlib import Path

import dalaran.blueprint as dlb

BLUEPRINTS = {
    "table_blueprint.rbl": [-1, 2],
    "table_blueprint2.rbl": [-2, 3],
}


def main() -> None:
    base = Path(__file__).parent

    for filename, x_range in BLUEPRINTS.items():
        blueprint = dlb.Blueprint(dlb.Spatial2DView(visual_bounds=dlb.VisualBounds2D(x_range=x_range, y_range=[-1, 2])))
        blueprint.save(f"e2e_{filename}", base / filename)


if __name__ == "__main__":
    main()
