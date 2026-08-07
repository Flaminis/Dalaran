"""Query and display the first 10 rows of a recording in a dataframe view."""

import sys

import dalaran as dl
import dalaran.blueprint as dlb

path_to_dlr = sys.argv[1]

dl.init("dalaran_example_dataframe_view_query", spawn=True)

dl.log_file_from_path(path_to_dlr)

blueprint = dlb.Blueprint(
    dlb.DataframeView(
        origin="/",
        query=dlb.archetypes.DataframeQuery(
            timeline="log_time",
            apply_latest_at=True,
        ),
    ),
)

dl.send_blueprint(blueprint)
