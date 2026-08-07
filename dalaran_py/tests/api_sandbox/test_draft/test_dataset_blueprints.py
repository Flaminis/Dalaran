from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import dalaran.blueprint as dlb
import dalaran_draft as dl

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path


@pytest.fixture
def rbl_factory(tmp_path_factory: pytest.TempPathFactory) -> Generator[Callable[[], Path], None, None]:
    def create_blueprint() -> Path:
        path = tmp_path_factory.mktemp("rbl") / "blueprint.rbl"
        blueprint = dlb.Blueprint(
            collapse_panels=True,
        )
        blueprint.save("dalaran_example_test", str(path))
        return path

    yield create_blueprint


def test_dataset_blueprints(rbl_factory: Callable[[], Path]) -> None:
    with dl.server.Server() as server:
        client = server.client()

        ds = client.create_dataset("basic_dataset")

        assert ds.default_blueprint() is None, "By default, no blueprint is set"

        # Register a default blueprint
        rbl_path = rbl_factory()
        ds.register_blueprint(rbl_path.as_uri())

        [rbl_name] = ds.blueprints()
        assert ds.default_blueprint() == rbl_name

        # Register another blueprint
        other_rbl_path = rbl_factory()
        ds.register_blueprint(other_rbl_path.as_uri(), set_default=False)

        assert ds.default_blueprint() == rbl_name, "The blueprint shouldn't have been changed"

        blueprint_list = ds.blueprints()
        assert len(blueprint_list) == 2, "There should be two registered blueprints"
        assert rbl_name in blueprint_list, "The first registered blueprint should still be there"
