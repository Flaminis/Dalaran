"""
Developer-experience command line tools shipped with the Dalaran SDK.

The modules in this package are deliberately dependency-free: they only use the
Python standard library (plus `numpy` where it is genuinely useful), and none of
them import the compiled `dalaran_bindings` extension at module level. That way
`dalaran-doctor` can still tell you *why* your installation is broken even when
the native parts of the SDK fail to load.

Entry points
------------
`dalaran-doctor`
    Environment diagnostic, see [dalaran.tools.doctor][].
`dalaran-init`
    Project scaffolding, see [dalaran.tools.scaffold][].
`dalaran-pack` / `dalaran-unpack`
    Portable `.dlrpack` dataset bundles, see [dalaran.tools.bundle][].

Example
-------
```python
from dalaran.tools.bundle import inspect_bundle

manifest = inspect_bundle("session.dlrpack")
print(manifest["dalaran_version"], len(manifest["files"]))
```

"""

from __future__ import annotations
