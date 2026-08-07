#!/usr/bin/env python3
"""Log a `TextLog`."""

import dalaran as dl

dl.init("dalaran_example_text_log", spawn=True)

dl.log("log", dl.TextLog("Application started.", level=dl.TextLogLevel.INFO))
