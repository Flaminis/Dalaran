#!/usr/bin/env python3
"""Examples of logging graph data to Dalaran and performing force-based layouts."""

from __future__ import annotations

import argparse
import itertools
import random

import numpy as np

import dalaran as dl
import dalaran.blueprint as dlb
from dalaran.blueprint.archetypes.force_collision_radius import ForceCollisionRadius
from dalaran.blueprint.archetypes.force_link import ForceLink
from dalaran.blueprint.archetypes.force_many_body import ForceManyBody

color_scheme = [
    [228, 26, 28, 255],  # Red
    [55, 126, 184, 255],  # Blue
    [77, 175, 74, 255],  # Green
    [152, 78, 163, 255],  # Purple
    [255, 127, 0, 255],  # Orange
    [255, 255, 51, 255],  # Yellow
    [166, 86, 40, 255],  # Brown
    [247, 129, 191, 255],  # Pink
    [153, 153, 153, 255],  # Gray
]

DESCRIPTION = """
# Graphs
This example shows various graph visualizations that you can create using Dalaran.
In this example, the node positions — and therefore the graph layout — are computed by Dalaran internally using a force-based layout algorithm.

You can modify how these graphs look by changing the parameters of the force-based layout algorithm in the selection panel.

The full source code for this example is available
[on GitHub](https://github.com/rerun-io/rerun/blob/latest/examples/python/graphs).
""".strip()


# We want reproducible results
random.seed(42)


def log_lattice(num_nodes: int) -> None:
    coordinates = itertools.product(range(num_nodes), range(num_nodes))

    nodes, colors = zip(
        *[
            (
                str(i),
                dl.components.Color([round((x / (num_nodes - 1)) * 255), round((y / (num_nodes - 1)) * 255), 0, 255]),
            )
            for i, (x, y) in enumerate(coordinates)
        ],
        strict=False,
    )

    dl.log(
        "lattice",
        dl.GraphNodes(
            nodes,
            colors=colors,
            labels=[f"({x}, {y})" for x, y in itertools.product(range(num_nodes), range(num_nodes))],
        ),
        static=True,
    )

    edges = []
    for x, y in itertools.product(range(num_nodes), range(num_nodes)):
        if y > 0:
            source = (y - 1) * num_nodes + x
            target = y * num_nodes + x
            edges.append((str(source), str(target)))
        if x > 0:
            source = y * num_nodes + (x - 1)
            target = y * num_nodes + x
            edges.append((str(source), str(target)))

    dl.log("lattice", dl.GraphEdges(edges, graph_type="directed"), static=True)


def log_trees() -> None:
    nodes = ["root"]
    radii = [42]
    colors = [[81, 81, 81, 255]]
    edges = []

    # Randomly add nodes and edges to the graph
    for i in range(50):
        existing = random.choice(nodes)
        new_node = str(i)
        nodes.append(new_node)
        radii.append(random.randint(10, 50))
        colors.append(random.choice(color_scheme))
        edges.append((existing, new_node))

        dl.set_time("frame", sequence=i)
        dl.log(
            "node_link",
            dl.GraphNodes(nodes, labels=nodes, radii=radii, colors=colors),
            dl.GraphEdges(edges, graph_type=dl.GraphType.Directed),
        )
        dl.log(
            "bubble_chart",
            dl.GraphNodes(nodes, labels=nodes, radii=radii, colors=colors),
        )


def log_markov_chain() -> None:
    transition_matrix = np.array([
        [0.8, 0.1, 0.1],  # Transitions from sunny
        [0.3, 0.4, 0.3],  # Transitions from rainy
        [0.2, 0.3, 0.5],  # Transitions from cloudy
    ])
    state_names = ["sunny", "rainy", "cloudy"]
    # For this example, we use hardcoded positions.
    positions = [[0, 0], [150, 150], [300, 0]]
    inactive_color = [153, 153, 153, 255]  # Gray
    active_colors = [
        [255, 127, 0, 255],  # Orange
        [55, 126, 184, 255],  # Blue
        [152, 78, 163, 255],  # Purple
    ]

    edges = [
        (state_names[i], state_names[j])
        for i in range(len(state_names))
        for j in range(len(state_names))
        if transition_matrix[i][j] > 0
    ]
    edges.append(("start", "sunny"))

    # We start in state "sunny"
    state = "sunny"

    for i in range(50):
        current_state_index = state_names.index(state)
        next_state_index = np.random.choice(range(len(state_names)), p=transition_matrix[current_state_index])
        state = state_names[next_state_index]
        colors = [inactive_color] * len(state_names)
        colors[next_state_index] = active_colors[next_state_index]

        dl.set_time("frame", sequence=i)
        dl.log(
            "markov_chain",
            dl.GraphNodes(state_names, labels=state_names, colors=colors, positions=positions),
            dl.GraphEdges(edges, graph_type="directed"),
        )


def log_blueprint() -> None:
    dl.send_blueprint(
        dlb.Blueprint(
            dlb.Grid(
                dlb.GraphView(
                    origin="node_link",
                    name="Node-link diagram",
                    force_link=ForceLink(distance=60),
                    force_many_body=ForceManyBody(strength=-60),
                ),
                dlb.GraphView(
                    origin="bubble_chart",
                    name="Bubble chart",
                    force_link=ForceLink(enabled=False),
                    force_many_body=ForceManyBody(enabled=False),
                    force_collision_radius=ForceCollisionRadius(enabled=True),
                    defaults=[dl.GraphNodes.from_fields(show_labels=False)],
                ),
                dlb.GraphView(
                    origin="lattice",
                    name="Lattice",
                    force_link=ForceLink(distance=60),
                    force_many_body=ForceManyBody(strength=-60),
                    defaults=[dl.GraphNodes.from_fields(show_labels=False, radii=10)],
                ),
                dlb.Horizontal(
                    dlb.GraphView(
                        origin="markov_chain",
                        name="Markov Chain",
                        # We don't need any forces for this graph, because the nodes have fixed positions.
                    ),
                    dlb.TextDocumentView(origin="description", name="Description"),
                ),
            ),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Logs various graphs using the Dalaran SDK.")
    dl.script_add_args(parser)
    args = parser.parse_args()

    dl.script_setup(args, "dalaran_example_graphs")
    dl.log("description", dl.TextDocument(DESCRIPTION, media_type=dl.MediaType.MARKDOWN), static=True)
    log_trees()
    log_lattice(10)
    log_markov_chain()
    log_blueprint()
    dl.script_teardown(args)


if __name__ == "__main__":
    main()
