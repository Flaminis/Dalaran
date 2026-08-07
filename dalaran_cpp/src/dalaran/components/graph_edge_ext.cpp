//#define EDIT_EXTENSION

#ifdef EDIT_EXTENSION
#include "graph_edge.hpp"

namespace dalaran {
    namespace components {

        // <CODEGEN_COPY_TO_HEADER>

        /// Create a new graph edge from a pair of strings.
        GraphEdge(dalaran::datatypes::Utf8 first_, dalaran::datatypes::Utf8 second_)
            : edge(std::move(first_), std::move(second_)) {}

        // </CODEGEN_COPY_TO_HEADER>

    } // namespace components
} // namespace dalaran

#endif
