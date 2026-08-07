from __future__ import annotations

import os


def _spawn_viewer(
    *,
    port: int = 9876,
    memory_limit: str = "75%",
    server_memory_limit: str = "1GiB",
    hide_welcome_screen: bool = False,
    detach_process: bool = True,
    executable_name: str = "dalaran",
    executable_path: str | None = None,
    headless: bool = False,
) -> int | None:
    """
    Internal helper to spawn a Dalaran Viewer, listening on the given port.

    Blocks until the viewer is ready to accept connections. Returns the spawned
    viewer's pid, or `None` if spawning was skipped (e.g. when
    `_DALARAN_TEST_FORCE_SAVE` is set).

    Used by [dalaran.spawn][] and [dalaran.experimental.ViewerClient][].

    Parameters
    ----------
    port:
        The port to listen on.
    memory_limit:
        An upper limit on how much memory the Dalaran Viewer should use.
        When this limit is reached, Dalaran will drop the oldest data.
        Example: `16GB` or `50%` (of system total).
    server_memory_limit:
        An upper limit on how much memory the gRPC server running
        in the same process as the Dalaran Viewer should use.
        When this limit is reached, Dalaran will drop the oldest data.
        Example: `16GB` or `50%` (of system total).

        Defaults to `1GiB`.
    hide_welcome_screen:
        Hide the normal Dalaran welcome screen.
    detach_process:
        Detach Dalaran Viewer process from the application process.
    executable_name:
        Specifies the name of the Dalaran executable.
        You can omit the `.exe` suffix on Windows.

        Defaults to `dalaran`.
    executable_path:
        Enforce a specific executable to use instead of searching
        through PATH for `executable_name`.

        Unspecified by default.
    headless:
        Run the spawned viewer in headless mode (no OS window).
        The viewer still listens for gRPC connections, so the SDK can keep
        logging data and request screenshots via
        [`dalaran.experimental.ViewerClient.save_screenshot`][].

    """

    import dalaran_bindings

    # NOTE: If `_DALARAN_TEST_FORCE_SAVE` is set, all recording streams will write to disk no matter
    # what, thus spawning a viewer is pointless (and probably not intended).
    if os.environ.get("_DALARAN_TEST_FORCE_SAVE") is not None:
        return None
    return dalaran_bindings.spawn(
        port=port,
        memory_limit=memory_limit,
        server_memory_limit=server_memory_limit,
        hide_welcome_screen=hide_welcome_screen,
        detach_process=detach_process,
        executable_name=executable_name,
        executable_path=executable_path,
        # Let the spawned dalaran process know it's just an app (skips analytics opt-in etc.).
        extra_env=[("DALARAN_APP_ONLY", "true")],
        headless=headless,
    )
