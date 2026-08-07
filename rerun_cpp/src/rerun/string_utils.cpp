#include "string_utils.hpp"

#include "c/rerun.h"

#include <string>

namespace rerun {
    namespace detail {
        dl_string to_dl_string(const std::string& str) {
            return to_dl_string(std::string_view(str));
        }

        dl_string to_dl_string(std::string_view str) {
            dl_string result;
            result.utf8 = str.data();
            result.length_in_bytes = static_cast<uint32_t>(str.length());
            return result;
        }

        dl_string to_dl_string(std::optional<std::string_view> str) {
            if (str.has_value()) {
                return to_dl_string(str.value());
            } else {
                dl_string result;
                result.utf8 = nullptr;
                result.length_in_bytes = 0;
                return result;
            }
        }
    } // namespace detail
} // namespace rerun
