#include "view_coordinates.hpp"

// <CODEGEN_COPY_TO_HEADER>
#include "view_dir.hpp"

// </CODEGEN_COPY_TO_HEADER>

// Uncomment for better auto-complete while editing the extension.
// #define EDIT_EXTENSION

namespace dalaran {
    namespace datatypes {

#ifdef EDIT_EXTENSION
        struct ViewCoordinatesExt {
            uint8_t coordinates[3];
#define ViewCoordinates ViewCoordinatesExt

            // <CODEGEN_COPY_TO_HEADER>

            /// Construct `ViewCoordinates` from x/y/z values.
            explicit constexpr ViewCoordinates(uint8_t axis0, uint8_t axis1, uint8_t axis2)
                : coordinates{
                      static_cast<dalaran::datatypes::ViewDir>(axis0),
                      static_cast<dalaran::datatypes::ViewDir>(axis1),
                      static_cast<dalaran::datatypes::ViewDir>(axis2)
                  } {}

            /// Construct `ViewCoordinates` from x/y/z enum values.
            explicit constexpr ViewCoordinates(
                dalaran::datatypes::ViewDir axis0, dalaran::datatypes::ViewDir axis1,
                dalaran::datatypes::ViewDir axis2
            )
                : coordinates{axis0, axis1, axis2} {}

            // </CODEGEN_COPY_TO_HEADER>
        };
#endif
    } // namespace datatypes
} // namespace dalaran
