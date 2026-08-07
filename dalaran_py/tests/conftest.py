"""
Test configuration for the Dalaran Python unit tests.

Some parts of the SDK are deliberately pure Python + numpy (`dalaran.robot`,
`dalaran.tools`, `dalaran.ros2`) so that they can be reasoned about, tested and
reviewed without the compiled `dalaran_bindings` extension. Importing them the
normal way still executes `dalaran/__init__.py`, which *does* require the native
extension, so in a source checkout without a build those tests would fail to
collect for reasons that have nothing to do with the code under test.

When the real package is unavailable we therefore register `dalaran` as a
namespace package pointing at the source tree, without executing its
`__init__.py`. Submodules that only need stdlib/numpy then import normally, and
anything that genuinely needs the bindings still fails loudly, as it should.
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

_SDK_ROOT = Path(__file__).resolve().parents[1] / "dalaran_sdk"
_PKG_ROOT = _SDK_ROOT / "dalaran"

# Pure-Python subpackages that must be importable without the native extension.
_BINDING_FREE_SUBPACKAGES = ("robot", "tools", "ros2")


def _install_namespace_shim() -> None:
    """Expose `dalaran.<pure subpackage>` without running `dalaran/__init__.py`."""
    if not _PKG_ROOT.is_dir():
        return

    shim = types.ModuleType("dalaran")
    shim.__path__ = [str(_PKG_ROOT)]
    shim.__doc__ = "Namespace shim for tests run without the native bindings."
    sys.modules["dalaran"] = shim

    for name in _BINDING_FREE_SUBPACKAGES:
        if not (_PKG_ROOT / name).is_dir():
            continue
        try:
            importlib.import_module(f"dalaran.{name}")
        except ImportError:
            # The subpackage genuinely needs something we do not have; let the
            # test that depends on it report the failure itself.
            sys.modules.pop(f"dalaran.{name}", None)


try:  # pragma: no cover - depends on whether the extension is built
    import dalaran  # noqa: F401
except ImportError:
    _install_namespace_shim()
