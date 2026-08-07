#include "spawn.hpp"
#include "c/dalaran.h"
#include "sdk_info.hpp"

namespace dalaran {
    Error spawn(const SpawnOptions& options) {
        DL_RETURN_NOT_OK(check_binary_and_header_version_match());

        dl_spawn_options dalaran_c_options = {};
        options.fill_dalaran_c_struct(dalaran_c_options);
        dl_error error = {};
        dl_spawn(&dalaran_c_options, &error);
        return Error(error);
    }
} // namespace dalaran
