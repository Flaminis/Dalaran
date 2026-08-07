"""
Test fixtures that let the ROS 2 converters run without ROS *or* the native bindings.

The converters build real Dalaran archetypes, which needs the compiled
`dalaran_bindings` extension. In a source checkout that extension may not exist,
so these fixtures swap `dalaran` for a recording stand-in whose every attribute
is an archetype factory. Combined with `Context(sink=...)`, that lets a test
assert on exactly what *would* have been logged.
"""

from __future__ import annotations

import importlib
import sys
import types
from typing import Any, NamedTuple

import pytest

# The converters reach into these for real math, so they must stay importable.
importlib.import_module("dalaran.robot")
importlib.import_module("dalaran.robot._math")


class FakeArchetype(NamedTuple):
    """A stand-in for a Dalaran archetype: just its name and its arguments."""

    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class _Factory:
    def __init__(self, name: str) -> None:
        self._name = name

    def __call__(self, *args: Any, **kwargs: Any) -> FakeArchetype:
        return FakeArchetype(self._name, args, kwargs)

    def __getattr__(self, item: str) -> Any:
        # Supports enum-ish access such as `dl.ViewCoordinates.RDF`.
        return f"{self._name}.{item}"


class _FakeModule(types.ModuleType):
    def __getattr__(self, item: str) -> Any:
        if item.startswith("_"):
            raise AttributeError(item)
        return _Factory(item)


@pytest.fixture
def _fake_dl(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Replace `dalaran` with a module whose attributes record their arguments."""
    real = sys.modules["dalaran"]

    fake = _FakeModule("dalaran")
    # Keep the real search path so `from dalaran.robot import ...` and friends
    # still resolve to the actual pure-Python helpers the converters rely on.
    fake.__path__ = list(getattr(real, "__path__", []))  # type: ignore[attr-defined]
    fake.components = _FakeModule("dalaran.components")  # type: ignore[attr-defined]
    fake.robot = sys.modules["dalaran.robot"]  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "dalaran", fake)
    return fake


class Captured:
    """The log calls a [`Context`][dalaran.ros2.Context] would have made."""

    def __init__(self) -> None:
        self.logs: list[Any] = []

    def __call__(self, record: Any) -> None:
        self.logs.append(record)

    @property
    def paths(self) -> list[str]:
        return [record.entity_path for record in self.logs]

    def by_path(self, entity_path: str) -> list[FakeArchetype]:
        return [
            archetype for record in self.logs if record.entity_path == entity_path for archetype in record.archetypes
        ]

    def names(self) -> list[str]:
        return [archetype.name for record in self.logs for archetype in record.archetypes]

    def first(self, name: str) -> FakeArchetype:
        for record in self.logs:
            for archetype in record.archetypes:
                if archetype.name == name:
                    return archetype
        msg = f"No {name} was logged; got {self.names()}"
        raise AssertionError(msg)


@pytest.fixture
def captured() -> Captured:
    """A sink that records every `Context.log` call."""
    return Captured()


@pytest.fixture
def ctx(captured: Captured) -> Any:
    """A [`Context`][dalaran.ros2.Context] that captures instead of logging."""
    from dalaran.ros2.context import Context

    return Context(sink=captured)
