#include "spawn.hpp"
#include "c/rerun.h"
#include "sdk_info.hpp"

namespace rerun {
    Error spawn(const SpawnOptions& options) {
        DL_RETURN_NOT_OK(check_binary_and_header_version_match());

        dl_spawn_options rerun_c_options = {};
        options.fill_rerun_c_struct(rerun_c_options);
        dl_error error = {};
        dl_spawn(&rerun_c_options, &error);
        return Error(error);
    }
} // namespace rerun
