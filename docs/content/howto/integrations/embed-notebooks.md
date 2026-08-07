---
title: Embed Dalaran in notebooks
order: 0
description: How to embed Dalaran in notebooks like Jupyter or Colab
---

Starting with version 0.15.1, Dalaran has improved support for embedding the Dalaran Viewer directly within IPython-style
notebooks. This makes it easy to iterate on API calls as well as to share data with others.

Dalaran has been tested with:

-   [Jupyter Notebook Classic](https://jupyter.org/)
-   [Jupyter Lab](https://jupyter.org/)
-   [VSCode](https://code.visualstudio.com/blogs/2021/08/05/notebooks)
-   [Google Colab](https://colab.research.google.com/)

To begin, install the `dalaran-sdk` package with the `notebook` extra:
```sh
pip install dalaran-sdk[notebook]
```

This installs both [dalaran-sdk](https://pypi.org/project/dalaran-sdk/) and [dalaran-notebook](https://pypi.org/project/dalaran-notebook/).

## The APIs

When using the Dalaran logging APIs, by default, the logged messages are buffered in-memory until
you send them to a sink such as via `dl.connect_grpc()` or `dl.save()`.

When using Dalaran in a notebook, rather than using the other sinks, you have the option to use [`dl.notebook_show()`](https://ref.dalaran.dev/docs/python/stable/common/initialization_functions/#dalaran.notebook_show). This method embeds the [web viewer](./embed-web.md) using the IPython `display` mechanism in the cell output, and sends the current recording data to it.

Once the viewer is open, any subsequent `dl.log()` calls will send their data directly to the viewer,
without any intermediate buffering.

For example:

```python
import dalaran as dl
from numpy.random import default_rng

dl.init("dalaran_example_notebook")

rng = default_rng(12345)

positions = rng.uniform(-5, 5, size=[10, 3])
colors = rng.uniform(0, 255, size=[10, 3])
radii = rng.uniform(0, 1, size=[10])

dl.log("random", dl.Points3D(positions, colors=colors, radii=radii))

dl.notebook_show()
```

<picture>
  <img src="https://static.rerun.io/notebook_example/e47920b7ca7988aba305d73b2aea2da7b81c93e3/full.png" alt="">
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/notebook_example/e47920b7ca7988aba305d73b2aea2da7b81c93e3/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/notebook_example/e47920b7ca7988aba305d73b2aea2da7b81c93e3/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/notebook_example/e47920b7ca7988aba305d73b2aea2da7b81c93e3/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/notebook_example/e47920b7ca7988aba305d73b2aea2da7b81c93e3/1200w.png">
</picture>

This is similar to calling `dl.connect_grpc()` or `dl.serve()` in that it configures the Dalaran SDK to send data to a viewer instance.

Note that the call to `dl.notebook_show()` drains the recording of its data. This means that any subsequent calls to `dl.notebook_show()`
will not result in the same data being displayed, because it has already been removed from the recording.
Support for this is tracked in [#6612](https://github.com/rerun-io/rerun/issues/6612).

If you wish to start a new recording, you can call `dl.init()` again.

The `notebook_show()` method also takes optional arguments for specifying the width and height of the viewer. For example:

```python
dl.notebook_show(width=400, height=400)
```

## Reacting to events in the Viewer

It is possible to register a callback to be triggered when certain Viewer events happen.

For example, here is how you can track which entities are currently selected in the Viewer:

```python
from dalaran.notebook import Viewer, ViewerEvent

selected_entities = []


def on_event(event: ViewerEvent):
    global selected_entities
    selected_entities = []  # clear the list

    if event.type == "selection_change":
        for item in event.items:
            if item.type == "entity":
                selected_entities.append(item.entity_path)


viewer = Viewer()
viewer.on_event(on_event)

display(viewer)
```

Whenever an entity is selected in the Viewer, `selected_entities.value` changes. The payload includes other useful information,
such as the position of the selection within a 2D or 3D view.

For a more complete example, see [callbacks.ipynb](https://github.com/Flaminis/Dalaran/blob/main/examples/python/notebook_callbacks/notebook_callbacks.ipynb).

## Working with blueprints

[Blueprints](../../getting-started/configure-the-viewer/navigating-the-viewer.md#programmatic-blueprints) can also be used with `notebook_show()` by providing a `blueprint`
parameter.

For example

```python
blueprint = dlb.Blueprint(
    dlb.Horizontal(dlb.Spatial3DView(origin="/world"), dlb.Spatial2DView(origin="/world/camera"), column_shares=[2, 1]),
)

dl.notebook_show(blueprint=blueprint)
```

Because blueprint types implement `_ipython_display_`, you can also just end any cell with a blueprint
object, and it will call `notebook_show()` behind the scenes.

```python
import numpy as np
import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_image")
rng = np.random.default_rng(12345)

image1 = rng.uniform(0, 255, size=[24, 64, 3])
image2 = rng.uniform(0, 255, size=[24, 64, 1])

dl.log("image1", dl.Image(image1))
dl.log("image2", dl.Image(image2))

dlb.Vertical(dlb.Spatial2DView(origin="/image1"), dlb.Spatial2DView(origin="/image2"))
```

<picture>
  <img src="https://static.rerun.io/notebook_blueprint_example/eb0663a9a8a0de8276390667a774acc1bc86148e/full.png" alt="">
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/notebook_blueprint_example/eb0663a9a8a0de8276390667a774acc1bc86148e/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/notebook_blueprint_example/eb0663a9a8a0de8276390667a774acc1bc86148e/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/notebook_blueprint_example/eb0663a9a8a0de8276390667a774acc1bc86148e/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/notebook_blueprint_example/eb0663a9a8a0de8276390667a774acc1bc86148e/1200w.png">
</picture>

## Streaming data

The notebook integration supports streaming data to the viewer during cell execution.

You can call `dl.notebook_show()` at any point after calling `dl.init()`, and any
`dl.log()` calls will be sent to the viewer in real-time.

```python
import math
from time import sleep

import numpy as np
import dalaran as dl
from dalaran.utilities import build_color_grid

dl.init("dalaran_example_notebook")
dl.notebook_show()

STEPS = 100
twists = math.pi * np.sin(np.linspace(0, math.tau, STEPS)) / 4
for t in range(STEPS):
    sleep(0.05)  # delay to simulate a long-running computation
    dl.set_time("step", sequence=t)
    cube = build_color_grid(10, 10, 10, twist=twists[t])
    dl.log("cube", dl.Points3D(cube.positions, colors=cube.colors, radii=0.5))
```

## Some working examples

To experiment with notebooks yourself, there are a few options.

### Running locally

The GitHub repo includes a [notebook example](https://github.com/Flaminis/Dalaran/blob/main/examples/python/notebook/cube.ipynb).

If you have a local checkout of Dalaran, you can:

```bash
$ cd examples/python/notebook
$ pip install -r requirements.txt
$ jupyter notebook cube.ipynb
```

This will open a browser window showing the notebook where you can follow along.

### Running in Google Colab

We also host a copy of the notebook in [Google Colab](https://colab.research.google.com/drive/1R9I7s4o6wydQC_zkybqaSRFTtlEaked_)

Note that if you copy and run the notebook yourself, the first Cell installs Dalaran into the Colab environment.
After running this cell you will need to restart the Runtime for the Dalaran package to show up successfully.

## Limitations

Browsers have limitations in the amount of memory usable by a single tab. If you are working with large datasets,
you may run into browser tab crashes due to out-of-memory errors.
If you encounter the issue, you can try to use the `save()` API to save the data to a file and share it as a standalone asset.

## Future work

We are actively working on improving the notebook experience and welcome any [feedback or suggestions](https://dalaran.dev/feedback).
The ongoing roadmap is being tracked in [GitHub issue #1815](https://github.com/rerun-io/rerun/issues/1815).
