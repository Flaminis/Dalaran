#include "sdk_info.hpp"
#include "c/dalaran.h"

#include <cstring> // strcmp
#include <string>

#include "c/dalaran.h"

namespace dalaran {
    const char* version_string() {
        return dl_version_string();
    }

    Error check_binary_and_header_version_match() {
        const char* binary_version = version_string();

        if (strcmp(binary_version, DALARAN_SDK_HEADER_VERSION) == 0) {
            return Error::ok();
        } else {
            return Error(
                ErrorCode::SdkVersionMismatch,
                std::string(
                    "Dalaran_c SDK version and SDK header/source versions don't match. "
                    "Make sure to link against the correct version of the dalaran_c library.\n"
                    "dalaran_c binary version:\n"
                )
                    .append(binary_version)
                    .append("\ndalaran_c header version:\n")
                    .append(DALARAN_SDK_HEADER_VERSION)
            );
        }
    }
} // namespace dalaran
