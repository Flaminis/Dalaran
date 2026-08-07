#include "clear.hpp"

// <CODEGEN_COPY_TO_HEADER>
#include "../dalaran_sdk_export.hpp"

// </CODEGEN_COPY_TO_HEADER>

// Uncomment for better auto-complete while editing the extension.
// #define EDIT_EXTENSION

namespace dalaran {
    namespace archetypes {

#ifdef EDIT_EXTENSION
        struct ClearExt {
            dalaran::components::ClearIsRecursive clear;

            // <CODEGEN_COPY_TO_HEADER>

            DALARAN_SDK_EXPORT static const Clear FLAT;

            DALARAN_SDK_EXPORT static const Clear RECURSIVE;

            Clear(bool _is_recursive = false)
                : Clear(components::ClearIsRecursive(_is_recursive)) {}

            // </CODEGEN_COPY_TO_HEADER>
        };
#endif

        const Clear Clear::FLAT = Clear(false);

        const Clear Clear::RECURSIVE = Clear(true);
    } // namespace archetypes
} // namespace dalaran
