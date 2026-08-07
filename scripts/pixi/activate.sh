#!/usr/bin/env bash
# Pixi activation script for Unix.
# Runs ensure-dalaran-env to set up the environment.

# ensure-dalaran-env may not exist yet on first activation (before package install).
# In that case, silently skip - it will run on next activation after install.
if command -v ensure-dalaran-env &> /dev/null; then
    ensure-dalaran-env
fi
