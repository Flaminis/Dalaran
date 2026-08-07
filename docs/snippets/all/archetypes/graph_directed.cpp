//! Log a simple directed graph.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_graph_directed");
    rec.spawn().exit_on_failure();

    rec.log(
        "simple",
        dalaran::GraphNodes({"a", "b", "c"})
            .with_positions({{0.0, 100.0}, {-100.0, 0.0}, {100.0, 0.0}})
            .with_labels({"A", "B", "C"}),
        dalaran::GraphEdges({{"a", "b"}, {"b", "c"}, {"c", "a"}})
            // Graphs are undirected by default.
            .with_graph_type(dalaran::GraphType::Directed)
    );
}
