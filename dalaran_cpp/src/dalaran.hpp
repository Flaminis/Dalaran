#pragma once

// Built-in Dalaran types (largely generated from an interface definition language)
#include "dalaran/archetypes.hpp"
#include "dalaran/components.hpp"
#include "dalaran/datatypes.hpp"

// Dalaran API.
#include "dalaran/collection.hpp"
#include "dalaran/collection_adapter.hpp"
#include "dalaran/collection_adapter_builtins.hpp"
#include "dalaran/component_descriptor.hpp"
#include "dalaran/config.hpp"
#include "dalaran/entity_path.hpp"
#include "dalaran/error.hpp"
#include "dalaran/image_utils.hpp"
#include "dalaran/recording_stream.hpp"
#include "dalaran/result.hpp"
#include "dalaran/sdk_info.hpp"
#include "dalaran/spawn.hpp"

/// All Dalaran C++ types and functions are in the `dalaran` namespace or one of its nested namespaces.
namespace dalaran {
    /// When an external [`Importer`] is asked to import some data that it doesn't know how to handle, it
    /// should exit with this exit code.
    // NOTE: Always keep in sync with other languages.
    constexpr int EXTERNAL_IMPORTER_INCOMPATIBLE_EXIT_CODE = 66;

    /// \deprecated Deprecated since 0.32.0. Use `EXTERNAL_IMPORTER_INCOMPATIBLE_EXIT_CODE` instead.
    [[deprecated("Deprecated since 0.32.0. Use EXTERNAL_IMPORTER_INCOMPATIBLE_EXIT_CODE instead."
    )]] constexpr int EXTERNAL_DATA_LOADER_INCOMPATIBLE_EXIT_CODE =
        EXTERNAL_IMPORTER_INCOMPATIBLE_EXIT_CODE;

    // Archetypes are the quick-and-easy default way of logging data to Dalaran.
    // Make them available in the dalaran namespace.
    using namespace archetypes;

    // Also import any component or datatype that has a unique name:
    using components::AlbedoFactor;
    using components::Color;
    using components::Colormap;
    using components::FillMode;
    using components::GeoLineString;
    using components::GraphType;
    using components::HalfSize2D;
    using components::HalfSize3D;
    using components::ImageBuffer;
    using components::KeyValuePairs;
    using components::LatLon;
    using components::LineStrip2D;
    using components::LineStrip3D;
    using components::MarkerShape;
    using components::MediaType;
    using components::Position2D;
    using components::Position3D;
    using components::Radius;
    using components::Scalar;
    using components::Text;
    using components::TextLogLevel;
    using components::TransformRelation;
    using components::TriangleIndices;
    using components::Vector2D;
    using components::Vector3D;

    using datatypes::Angle;
    using datatypes::AnnotationInfo;
    using datatypes::ChannelDatatype;
    using datatypes::ClassDescription;
    using datatypes::ColorModel;
    using datatypes::DVec2D;
    using datatypes::Float32;
    using datatypes::KeypointPair;
    using datatypes::Mat3x3;
    using datatypes::PixelFormat;
    using datatypes::Quaternion;
    using datatypes::Rgba32;
    using datatypes::RotationAxisAngle;
    using datatypes::TensorBuffer;
    using datatypes::TensorData;
    using datatypes::Vec2D;
    using datatypes::Vec3D;
    using datatypes::Vec4D;

    // Document namespaces that span several files:

    /// All built-in archetypes. See [Types](https://www.dalaran.dev/docs/reference/types) in the Dalaran manual.
    namespace archetypes {}

    /// All built-in components. See [Types](https://www.dalaran.dev/docs/reference/types) in the Dalaran manual.
    namespace components {}

    /// All built-in datatypes. See [Types](https://www.dalaran.dev/docs/reference/types) in the Dalaran manual.
    namespace datatypes {}

    /// All blueprint types. This is still experimental and subject to change!
    namespace blueprint {}
} // namespace dalaran
