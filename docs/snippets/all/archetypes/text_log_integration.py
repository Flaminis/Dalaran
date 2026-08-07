"""Shows integration of Dalaran's `TextLog` with Python's `logging` module."""

import logging

import dalaran as dl

dl.init("dalaran_example_text_log_integration", spawn=True)

# Log a text entry directly
dl.log(
    "logs",
    dl.TextLog("this entry has loglevel TRACE", level=dl.TextLogLevel.TRACE),
)

# Or log via a logging handler
logging.getLogger().addHandler(dl.LoggingHandler("logs/handler"))
logging.getLogger().setLevel(-1)
logging.info("This INFO log got added through the standard logging interface")
