"""
Import helpers for the `dalaran.tools` CLI tests.

The command line tools are pure standard library on purpose, so they must work
even when the compiled `dalaran_bindings` extension is not built. `import
dalaran.tools.bundle` would execute `dalaran/__init__.py`, which does need the
extension, so we fall back to loading the module straight from its file when the
package cannot be imported. That keeps these tests runnable in a source
checkout without a native build.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

_TOOLS_DIR = Path(__file__).resolve().parents[3] / "dalaran_sdk" / "dalaran" / "tools"


def load_tool(name: str) -> ModuleType:
    """Import `dalaran.tools.<name>`, falling back to a standalone file import."""
    try:
        return importlib.import_module(f"dalaran.tools.{name}")
    except ImportError:
        pass

    package = "_dalaran_tools_standalone"
    if package not in sys.modules:
        spec = importlib.util.spec_from_file_location(package, _TOOLS_DIR / "__init__.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        module.__path__ = [str(_TOOLS_DIR)]  # type: ignore[attr-defined]
        sys.modules[package] = module
        spec.loader.exec_module(module)

    return importlib.import_module(f"{package}.{name}")
