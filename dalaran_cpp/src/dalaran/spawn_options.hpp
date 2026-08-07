#pragma once

#include <cstdint>
#include <string_view>

extern "C" struct dl_spawn_options;

namespace dalaran {

    /// Options to control the behavior of `spawn`.
    ///
    /// Refer to the field-level documentation for more information about each individual options.
    ///
    /// The defaults are ok for most use cases.
    ///
    /// Keep this in sync with dalaran.h's `dl_spawn_options`.
    struct SpawnOptions {
        /// The port to listen on.
        uint16_t port = 9876;

        /// An upper limit on how much memory the Dalaran Viewer should use.
        ///
        /// When this limit is reached, Dalaran will drop the oldest data.
        /// Example: `16GB` or `50%` (of system total).
        ///
        /// Defaults to `75%` if unset.
        std::string_view memory_limit = "75%";

        /// An upper limit on how much memory the gRPC server running
        /// in the same process as the Dalaran Viewer should use.
        /// When this limit is reached, Dalaran will drop the oldest data.
        /// Example: `16GB` or `50%` (of system total).
        ///
        /// Defaults to `1GiB`.
        std::string_view server_memory_limit = "1GiB";

        /// Hide the normal Dalaran welcome screen.
        ///
        /// Defaults to `false` if unset.
        bool hide_welcome_screen = false;

        /// Detach Dalaran Viewer process from the application process.
        ///
        /// Defaults to `true` if unset.
        bool detach_process = true;

        /// Specifies the name of the Dalaran executable.
        ///
        /// You can omit the `.exe` suffix on Windows.
        ///
        /// Defaults to `dalaran` if unset.
        std::string_view executable_name = "dalaran";

        /// Enforce a specific executable to use instead of searching through PATH
        /// for `SpawnOptions::executable_name`.
        std::string_view executable_path;

        /// Convert to the corresponding dalaran_c struct for internal use.
        ///
        /// _Implementation note:_
        /// By not returning it we avoid including the C header in this header.
        /// \private
        void fill_dalaran_c_struct(dl_spawn_options& spawn_opts) const;
    };
} // namespace dalaran
