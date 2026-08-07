"""Create and log a bar chart."""

import dalaran as dl

dl.init("dalaran_example_bar_chart", spawn=True)
dl.log("bar_chart", dl.BarChart([8, 4, 0, 9, 1, 4, 1, 6, 9, 0]))
dl.log(
    "bar_chart_custom_abscissa",
    dl.BarChart([8, 4, 0, 9, 1, 4], abscissa=[0, 1, 3, 4, 7, 11]),
)
dl.log(
    "bar_chart_custom_abscissa_and_widths",
    dl.BarChart(
        [8, 4, 0, 9, 1, 4],
        abscissa=[0, 1, 3, 4, 7, 11],
        widths=[1, 2, 1, 3, 4, 1],
    ),
)
