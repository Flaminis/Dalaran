#include <utility>
#include "utf8pair.hpp"

// #define EDIT_EXTENSION

namespace dalaran {
    namespace datatypes {

#ifdef EDIT_EXTENSION
        // <CODEGEN_COPY_TO_HEADER>

        /// Creates a string pair.
        Utf8Pair(dalaran::datatypes::Utf8 first_, dalaran::datatypes::Utf8 second_)
            : first(std::move(first_)), second(std::move(second_)) {}

        // </CODEGEN_COPY_TO_HEADER>
#endif
    } // namespace datatypes
} // namespace dalaran
