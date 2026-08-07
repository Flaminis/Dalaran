#include "component_type.hpp"
#include "c/dalaran.h"
#include "string_utils.hpp"

#include <arrow/c/bridge.h>

namespace dalaran {
    Result<ComponentTypeHandle> ComponentType::register_component() const {
        dl_component_type type;
        type.descriptor.archetype = detail::to_dl_string(descriptor.archetype);
        type.descriptor.component = detail::to_dl_string(descriptor.component);
        type.descriptor.component_type = detail::to_dl_string(descriptor.component_type);
        ARROW_RETURN_NOT_OK(arrow::ExportType(*arrow_datatype, &type.schema));

        dl_error error = {};
        auto handle = dl_register_component_type(type, &error);
        if (error.code != DL_ERROR_CODE_OK) {
            return Error(error);
        }

        return handle;
    }
} // namespace dalaran
