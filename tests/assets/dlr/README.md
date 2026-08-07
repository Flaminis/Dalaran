`.dlr` files that are checked in to `git lfs`. We use this to ensure we can still load old `.dlr` files.

We don't yet guarantee backwards compatibility, but we at least check it so that we _know_ if/when we break it.

### Verifying
To verify that they all still load, run:

> pixi run check-backwards-compatibility


### Updating
To update the contents of this folder, run:

> tests/assets/dlr/generate-compatibility-rrds.sh
