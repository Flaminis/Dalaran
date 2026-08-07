"""Use a blueprint to show a bar chart."""

import dalaran as dl
import dalaran.blueprint as dlb

dl.init("dalaran_example_bar_chart", spawn=True)
dl.log("bar_chart", dl.BarChart([8, 4, 0, 9, 1, 4, 1, 6, 9, 0]))

# Create a bar chart view to display the chart.
blueprint = dlb.Blueprint(
    dlb.BarChartView(
        origin="bar_chart",
        name="Bar Chart",
        background=dlb.archetypes.PlotBackground(
            color=[50, 0, 50, 255], show_grid=False
        ),
    ),
    collapse_panels=True,
)

dl.send_blueprint(blueprint)
