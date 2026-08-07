"""Every costmap docstring example must actually run."""

from __future__ import annotations

import re
from pathlib import Path

import dalaran.ros2.costmap as costmap_module

_CODE_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)


def docstring_examples() -> list[str]:
    """Return the runnable python blocks in `dalaran/ros2/costmap.py`."""
    source = Path(costmap_module.__file__).read_text(encoding="utf-8")
    blocks = []
    for block in _CODE_BLOCK.findall(source):
        code = "\n".join(line.removeprefix("    ") for line in block.splitlines())
        if "dl.init" in code:
            # Needs a live recording, and therefore the native bindings.
            continue
        blocks.append(code)
    return blocks


def test_the_module_documents_itself_with_examples() -> None:
    assert len(docstring_examples()) >= 8


def test_every_runnable_docstring_example_works() -> None:
    for code in docstring_examples():
        exec(compile(code, "<costmap docstring>", "exec"), {})  # noqa: S102
