// General information about the SDK.
#pragma once

#include <cstdint> // uint32_t etc.
#include <optional>
#include <string_view>

#include "error.hpp"
#include "spawn_options.hpp"

namespace dalaran {
    /// Spawns a new Dalaran Viewer process from an executable available in PATH, ready to
    /// listen for incoming gRPC connections.
    ///
    /// If a Dalaran Viewer is already listening on this gRPC port, the stream will be redirected to
    /// that viewer instead of starting a new one.
    ///
    /// options:
    /// See `dalaran::SpawnOptions` for more information.
    Error spawn(const SpawnOptions& options = {});
} // namespace dalaran
