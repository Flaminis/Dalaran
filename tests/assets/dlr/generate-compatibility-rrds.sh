#!/usr/bin/env bash
# Generate and check in .dlr files used for backwards compatibility tests.

set -eux

DEST_DIR="tests/assets/dlr"

# Uncomment if you want to update _ALL_ files (not recommended!)
# echo "Removing old rrds…"
# find "${DEST_DIR}" -type f -name "*.dlr" -delete

# TODO(emilk): only update missing files
echo "Generating example .dlr files…"
pixi run build-examples dlr --install --channel main "${DEST_DIR}/examples"

echo "Generating snippet .dlr files…"
pixi run uvpy docs/snippets/compare_snippet_output.py --no-py --no-cpp --write-missing-backward-assets

echo "Adding new .dlr files to git…"
find "${DEST_DIR}" -type f -name "*.dlr" -exec git add -f {} \;

echo "!!! It is recommended that you ONLY _add_ files, NEVER remove them"
