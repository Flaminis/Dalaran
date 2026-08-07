#include "timeline.hpp"

#include "c/dalaran.h"
#include "string_utils.hpp"

namespace dalaran {
    Error Timeline::to_c_ffi_struct(dl_timeline& out_column) const {
        switch (type) {
            case TimeType::Sequence:
                out_column.type = DL_TIME_TYPE_SEQUENCE;
                break;
            case TimeType::Duration:
                out_column.type = DL_TIME_TYPE_DURATION;
                break;
            case TimeType::Timestamp:
                out_column.type = DL_TIME_TYPE_TIMESTAMP;
                break;
            default:
                return Error(
                    ErrorCode::InvalidEnumValue,
                    "Invalid TimeType" + std::to_string(static_cast<int>(type))
                );
        }
        out_column.name = detail::to_dl_string(name);

        return Error::ok();
    }
} // namespace dalaran
