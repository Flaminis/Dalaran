//! Log a simple undirected graph.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_graph_undirected")
            .spawn()?;

    rec.log(
        "simple",
        &[
            &dalaran::GraphNodes::new(["a", "b", "c"])
                .with_positions([(0.0, 100.0), (-100.0, 0.0), (100.0, 0.0)])
                .with_labels(["A", "B", "C"])
                as &dyn dalaran::AsComponents,
            &dalaran::GraphEdges::new([("a", "b"), ("b", "c"), ("c", "a")])
                // Optional: graphs are undirected by default.
                .with_undirected_edges(),
        ],
    )?;

    Ok(())
}
