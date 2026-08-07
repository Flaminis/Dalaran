#include "config.hpp"

namespace dalaran {

    DalaranGlobalConfig& DalaranGlobalConfig::instance() {
        static DalaranGlobalConfig global;
        return global;
    }

    DalaranGlobalConfig::DalaranGlobalConfig() : default_enabled(true) {}
} // namespace dalaran
