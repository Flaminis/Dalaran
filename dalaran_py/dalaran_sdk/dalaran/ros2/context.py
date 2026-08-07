"""
The logging context handed to every ROS 2 message converter.

A [`Context`][dalaran.ros2.context.Context] carries the things a converter needs
but should not own: which recording to log to, the shared transform tree that
`/tf` feeds, and the entity path prefix. It also owns the single choke point
through which converters emit data, which means a test can swap in a recording
sink and assert on exactly what *would* have been logged without a viewer, a
recording, or the native bindings being present.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__all__ = ["Context", "RecordedLog"]

if TYPE_CHECKING:
    from collections.abc import Callable

    from dalaran.robot import TransformTree


class RecordedLog(tuple):
    """
    One captured `log` call: `(entity_path, archetypes, static)`.

    Only produced when a [`Context`][dalaran.ros2.context.Context] has a `sink`
    installed. It is a plain tuple, so it unpacks and compares like one.
    """

    __slots__ = ()

    def __new__(cls, entity_path: str, archetypes: tuple[Any, ...], static: bool) -> RecordedLog:
        return super().__new__(cls, (entity_path, archetypes, static))

    @property
    def entity_path(self) -> str:
        """The entity path the data was logged to."""
        return self[0]

    @property
    def archetypes(self) -> tuple[Any, ...]:
        """The archetypes that were logged."""
        return self[1]

    @property
    def static(self) -> bool:
        """Whether the data was logged as static."""
        return self[2]


class Context:
    """
    Shared state for a batch of ROS 2 message conversions.

    Parameters
    ----------
    recording:
        The [`dalaran.RecordingStream`][] to log to. `None` uses the current
        active recording.
    prefix:
        Entity path prefix for everything this context logs.
    tree:
        The [`dalaran.robot.TransformTree`][] that `/tf` and `/tf_static`
        messages drive. One is created lazily on first use if not given.
    frame_entity_paths:
        Optional mapping from ROS `frame_id` to entity path, used to place
        sensor data on the frame it was measured in. Populated automatically as
        `/tf` messages arrive.
    sink:
        Test/inspection hook. When set, it is called instead of
        [`dalaran.log`][] with a [`RecordedLog`][dalaran.ros2.context.RecordedLog].

    Examples
    --------
    ```python
    from dalaran.ros2.context import Context

    captured = []
    ctx = Context(sink=captured.append)
    ctx.log("scan", "not-really-an-archetype")
    assert captured[0].entity_path == "scan"
    ```

    """

    def __init__(
        self,
        *,
        recording: Any = None,
        prefix: str = "",
        tree: TransformTree | None = None,
        frame_entity_paths: dict[str, str] | None = None,
        sink: Callable[[RecordedLog], None] | None = None,
    ) -> None:
        self.recording = recording
        self.prefix = prefix.strip("/")
        self.sink = sink
        self.frame_entity_paths: dict[str, str] = frame_entity_paths if frame_entity_paths is not None else {}
        self._tree = tree

    @property
    def tree(self) -> TransformTree:
        """
        The transform tree `/tf` messages are replayed into.

        Created on first access so that a context which never sees a transform
        never needs `dalaran.robot` at all.
        """
        if self._tree is None:
            from dalaran.robot import TransformTree

            self._tree = TransformTree(root="world", prefix=self.prefix or None, recording=self.recording)
        return self._tree

    @property
    def has_tree(self) -> bool:
        """Whether a transform tree has been created yet."""
        return self._tree is not None

    def entity_path(self, *parts: str) -> str:
        """Join `parts` into an entity path below this context's prefix."""
        from .naming import entity_path_join

        return entity_path_join(self.prefix, *parts)

    def frame_path(self, frame_id: str, fallback: str) -> str:
        """
        Return the entity path that `frame_id` maps to, or `fallback`.

        Sensor messages carry the frame they were measured in, not the entity
        they belong to. Once `/tf` has told us where a frame lives, this puts
        the data straight onto it; until then the topic-derived path is used.
        """
        if not frame_id:
            return fallback
        return self.frame_entity_paths.get(frame_id.lstrip("/"), fallback)

    def log(self, entity_path: str, *archetypes: Any, static: bool = False) -> None:
        """
        Log `archetypes` to `entity_path`, honoring this context's sink and recording.

        Examples
        --------
        ```python
        from dalaran.ros2.context import Context

        captured: list = []
        ctx = Context(prefix="robots/spot", sink=captured.append)
        ctx.log(ctx.entity_path("scan"), "archetype-goes-here")
        assert captured[0].entity_path == "robots/spot/scan"
        ```

        """
        if self.sink is not None:
            self.sink(RecordedLog(entity_path, tuple(archetypes), static))
            return

        import dalaran as dl

        dl.log(entity_path, *archetypes, static=static, recording=self.recording)

    def set_time(self, timeline: str, **kwargs: Any) -> None:
        """Set a timeline's current time, unless a sink is capturing this context."""
        if self.sink is not None:
            return

        import dalaran as dl

        dl.set_time(timeline, recording=self.recording, **kwargs)
