"""Use a blueprint to show a text log."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_text_log", spawn=True)

dl.set_time("time", sequence=0)
dl.log(
    "log/status", dl.TextLog("Application started.", level=dl.TextLogLevel.INFO)
)
dl.set_time("time", sequence=5)
dl.log("log/other", dl.TextLog("A warning.", level=dl.TextLogLevel.WARN))
for i in range(10):
    dl.set_time("time", sequence=i)
    dl.log(
        "log/status",
        dl.TextLog(f"Processing item {i}.", level=dl.TextLogLevel.INFO),
    )

# Create a text view that displays all logs.
blueprint = dlb.Blueprint(
    dlb.TextLogView(
        origin="/log",
        name="Text Logs",
        columns=dlb.TextLogColumns(
            timeline_columns=["time"],
            text_log_columns=["loglevel", "entitypath", "body"],
        ),
        rows=dlb.TextLogRows(
            filter_by_log_level=["INFO", "WARN", "ERROR"],
        ),
        format_options=dlb.TextLogFormat(
            monospace_body=False,
        ),
    ),
    collapse_panels=True,
)

dl.send_blueprint(blueprint)
