from __future__ import annotations

import importlib
from unittest.mock import Mock, patch

import pytest
import dalaran.utilities.datafusion.functions.url_generation
from dalaran.error_utils import DalaranMissingDependencyError


def test_smoke() -> None:
    """Just check that we can import the module."""


def test_segment_url_import_normal() -> None:
    """Check that we can import segment_url when datafusion is available."""
    from dalaran.utilities.datafusion.functions.url_generation import segment_url

    assert segment_url is not None


def test_segment_url_without_datafusion() -> None:
    """Check that calling segment_url raises DalaranOptionalDependencyError when datafusion is unavailable."""
    # Mock the import to make datafusion unavailable
    with patch.dict("sys.modules", {"datafusion": None}):
        importlib.reload(dalaran.utilities.datafusion.functions.url_generation)
        # Import the module - this should work
        from dalaran.utilities.datafusion.functions.url_generation import segment_url

        # Create a mock dataset for testing
        mock_dataset = Mock()

        # But calling the function should raise an error
        with pytest.raises(DalaranMissingDependencyError, match="'datafusion' could not be imported"):
            segment_url(mock_dataset)
