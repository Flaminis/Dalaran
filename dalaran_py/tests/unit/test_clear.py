from __future__ import annotations

import numpy as np
import dalaran as dl
from dalaran.components import ClearIsRecursive, ClearIsRecursiveBatch


def test_clear() -> None:
    recursive = True

    print(f"dl.Clear(\nrecursive={recursive}\n)")
    arch = dl.Clear(recursive=recursive)
    print(f"{arch}\n")

    assert arch.is_recursive == ClearIsRecursiveBatch([True])


def test_clear_factory_methods() -> None:
    assert dl.Clear(recursive=True) == dl.Clear.recursive()
    assert dl.Clear(recursive=False) == dl.Clear.flat()


def test_truthiness() -> None:
    assert ClearIsRecursive(recursive=True)
    assert not ClearIsRecursive(recursive=False)

    assert np.array_equal(
        np.array([ClearIsRecursive(recursive=True), ClearIsRecursive(recursive=False)], dtype=np.bool_),
        np.array([True, False], dtype=np.bool_),
    )


if __name__ == "__main__":
    test_clear()
