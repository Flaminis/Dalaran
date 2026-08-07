<!--[metadata]
title = "Notebook: viewer"
description = "Embed a pre-recorded DLR inside a Jupyter notebook with the Dalaran viewer widget. Great for demos and docs."
tags = ["Notebook", "Widget", "3D"]
thumbnail = "https://static.rerun.io/notebook_viewer/3e3bc9c7eede26db837fb317b7e2b2de77dfc777/480w.png"
thumbnail_dimensions = [480, 272]
channel = "main"
include_in_manifest = true
-->

## Overview

This notebook shows the easiest way to embed the Dalaran Viewer widget inside a Jupyter notebook. Instead of logging new data, it loads a pre-recorded `.dlr` file and renders the scene inline, making it perfect for demos, documentation, or quick inspections of existing captures.

You need the separate support package [`dalaran-notebook`](https://pypi.org/project/dalaran-notebook/) to use this feature. Typically this is installed using:

```bash
pip install "dalaran-sdk[notebook]"
```

Check out the [minimal notebook example](https://dalaran.dev/examples/integrations/notebook) for a quick start.

## Background

In this notebook we are loading a pre-recorded `.dlr` file into the Dalaran Viewer widget. The viewer streams the capture and allows you to interact with the 3D scene directly in your browser. You can orbit, zoom, and inspect the scene without needing to run any additional applications.

## Running in Jupyter

First, install the requirements (this includes Jupyter, the Dalaran SDK, and the notebook support package):

```bash
pip install -r requirements.txt
```

Then, open the notebook:

```bash
jupyter notebook notebook_viewer.ipynb
```

When the notebook launches, the embedded viewer will stream the remote mesh capture so you can orbit, zoom, and inspect the scene directly inside the notebook.
