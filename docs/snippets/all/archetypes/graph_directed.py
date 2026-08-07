"""Log a simple directed graph."""

import dalaran as dl

dl.init("dalaran_example_graph_directed", spawn=True)

dl.log(
    "simple",
    dl.GraphNodes(
        node_ids=["a", "b", "c"],
        positions=[(0.0, 100.0), (-100.0, 0.0), (100.0, 0.0)],
        labels=["A", "B", "C"],
    ),
    dl.GraphEdges(
        edges=[("a", "b"), ("b", "c"), ("c", "a")], graph_type="directed"
    ),
)
