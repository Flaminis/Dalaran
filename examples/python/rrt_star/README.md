<!--[metadata]
title = "RRT*"
description = "Visualize the RRT* sampling-based path planner: watch the tree expand and re-wire toward an optimal route."
tags = ["2D"]
thumbnail= "https://static.rerun.io/rrt-star/fbbda33bdbbfa469ec95c905178ac3653920473a/480w.png"
thumbnail_dimensions = [480, 480]
channel = "main"
include_in_manifest = true
-->

This example visualizes the path finding algorithm RRT\* in a simple environment.

<picture>
  <img src="https://static.rerun.io/rrt-star/4d4684a24eab7d5def5768b7c1685d8b1cb2c010/full.png" alt="RRT* example screenshot">
  <source media="(max-width: 480px)" srcset="https://static.rerun.io/rrt-star/4d4684a24eab7d5def5768b7c1685d8b1cb2c010/480w.png">
  <source media="(max-width: 768px)" srcset="https://static.rerun.io/rrt-star/4d4684a24eab7d5def5768b7c1685d8b1cb2c010/768w.png">
  <source media="(max-width: 1024px)" srcset="https://static.rerun.io/rrt-star/4d4684a24eab7d5def5768b7c1685d8b1cb2c010/1024w.png">
  <source media="(max-width: 1200px)" srcset="https://static.rerun.io/rrt-star/4d4684a24eab7d5def5768b7c1685d8b1cb2c010/1200w.png">
</picture>

## Used Dalaran types
[`LineStrips2D`](https://www.dalaran.dev/docs/reference/types/archetypes/line_strips2d), [`Points2D`](https://www.dalaran.dev/docs/reference/types/archetypes/points2d), [`TextDocument`](https://www.dalaran.dev/docs/reference/types/archetypes/text_document)

## Background
The algorithm finds a path between two points by randomly expanding a tree from the start point.
After it has added a random edge to the tree it looks at nearby nodes to check if it's faster to reach them through this new edge instead,
and if so it changes the parent of these nodes. This ensures that the algorithm will converge to the optimal path given enough time.

A detailed explanation can be found in the original paper
Karaman, S. Frazzoli, S. 2011. "Sampling-based algorithms for optimal motion planning".
or in [this medium article](https://theclassytim.medium.com/robotic-path-planning-rrt-and-rrt-212319121378)


## Logging and visualizing with Dalaran

All points are logged using the [`Points2D`](https://www.dalaran.dev/docs/reference/types/archetypes/points2d) archetype, while the lines are logged using the LineStrips2D [`LineStrips2D`](https://www.dalaran.dev/docs/reference/types/archetypes/line_strips2d).

The visualizations in this example were created with the following Dalaran code:

### Map

#### Starting point
```python
dl.log("map/start", dl.Points2D([start_point], radii=0.02, colors=[[255, 255, 255, 255]]))
```

#### Destination point
```python
dl.log("map/destination", dl.Points2D([end_point], radii=0.02, colors=[[255, 255, 0, 255]]))
```

#### Obstacles
```python
dl.log("map/obstacles", dl.LineStrips2D(self.obstacles))
```


### RRT tree

#### Edges
```python
dl.log("map/tree/edges", dl.LineStrips2D(tree.segments(), radii=0.0005, colors=[0, 0, 255, 128]))
```

#### New edges
```python
dl.log("map/new/new_edge", dl.LineStrips2D([(closest_node.pos, new_point)], colors=[color], radii=0.001))
```

#### Vertices
```python
dl.log(
    "map/tree/vertices",
    dl.Points2D([node.pos for node in tree], radii=0.002),
    dl.AnyValues(cost=[float(node.cost) for node in tree]),
)
```

#### Close nodes
```python
dl.log("map/new/close_nodes", dl.Points2D([node.pos for node in close_nodes]))
```

#### Closest node
```python
dl.log("map/new/closest_node", dl.Points2D([closest_node.pos], radii=0.008))
```

#### Random points
```python
dl.log("map/new/random_point", dl.Points2D([random_point], radii=0.008))
```

#### New points
```python
dl.log("map/new/new_point", dl.Points2D([new_point], radii=0.008))
```

#### Path
```python
dl.log("map/path", dl.LineStrips2D(segments, radii=0.002, colors=[0, 255, 255, 255]))
```


## Run the code
To run this example, make sure you have the Dalaran repository checked out and the latest SDK installed:
```bash
pip install --upgrade dalaran-sdk  # install the latest Dalaran SDK
git clone git@github.com:Flaminis/Dalaran.git  # Clone the repository
cd dalaran
git checkout latest  # Check out the commit matching the latest SDK release
```
Install the necessary libraries specified in the requirements file:
```bash
pip install -e examples/python/rrt_star
```
To experiment with the provided example, simply execute the main Python script:
```bash
python -m rrt_star # run the example
```
If you wish to customize it, explore additional features, or save it use the CLI with the `--help` option for guidance:
```bash
python -m rrt_star --help
```
