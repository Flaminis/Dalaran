---
title: Migrating from 0.32 to 0.33
order: 977
hidden: true
---

## `dalaran-sdk[dataplatform]` and `dalaran-sdk[datafusion]` renamed to `dalaran-sdk[catalog]`

The Python optional-dependency extra for catalog/query API tools has been renamed to `catalog`.

| Before                       | After                 |
|------------------------------|-----------------------|
| `pip install dalaran-sdk[dataplatform]` | `pip install dalaran-sdk[catalog]` |
| `pip install dalaran-sdk[datafusion]`   | `pip install dalaran-sdk[catalog]` |

The old `dataplatform` and `datafusion` extras still resolve to the same set of dependencies for backwards compatibility, but will be removed in a future release. <!-- NOLINT -->
Update any `pyproject.toml`, `requirements.txt`, or install scripts to the new name.
