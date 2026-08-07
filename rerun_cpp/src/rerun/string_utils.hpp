
#pragma once

#include <optional>
#include <string>
#include <string_view>

struct dl_string;

namespace rerun {
    namespace detail {
        dl_string to_dl_string(const std::string& str);
        dl_string to_dl_string(std::string_view str);
        dl_string to_dl_string(std::optional<std::string_view> str);
    } // namespace detail
} // namespace rerun
