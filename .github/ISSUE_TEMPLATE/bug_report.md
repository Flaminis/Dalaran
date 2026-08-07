---
name: Bug report
about: Something is broken, crashes, or produces the wrong result
title: ''
labels: 🪳 bug, 👀 needs triage
assignees: ''

---

<!--
Please search existing issues first. If your problem is already reported,
add a 👍 and any new information you have rather than opening a duplicate.
-->

## What happened

<!-- What did you observe? A screenshot, GIF or short video helps a lot for
anything visual. -->

## What you expected to happen

## Reproduction

<!-- The single most useful thing you can provide. Ideally a minimal script and,
if the problem depends on the data, a small .dlr recording or bag we can open.
Attach files directly to the issue if they are small enough. -->

```python
import dalaran as dl
# minimal script that shows the problem
```

Steps:

1.
2.
3.

## Environment

- Dalaran version: <!-- output of `dalaran --version` -->
- SDK and version: <!-- e.g. Python dalaran-sdk 0.x, Rust dalaran 0.x, C++ -->
- Installed how: <!-- pip, cargo install, built from source (commit hash) -->
- OS and architecture: <!-- e.g. Ubuntu 24.04 x86_64, macOS 15 arm64 -->
- GPU and driver: <!-- required for anything that renders; `dalaran --version` reports it -->
- Running in: <!-- native viewer, web viewer + browser version, notebook, headless -->

## Backtrace or logs

<!-- If it crashed, paste the backtrace. Re-running with `RUST_LOG=debug` (or
`trace`) often makes the cause obvious. -->

```
```

## Does it also happen upstream?

<!-- Optional, and only if it is easy for you to check. Dalaran is a fork of
Rerun, and knowing whether a bug is ours or inherited helps us route the fix
and send it upstream when it belongs there. -->

## Additional context
