// NOTE: Have a look at `dl_sdk/src/lib.rs` for an accurate listing of all these symbols.
pub use dl_sdk::*;

/// Transform helpers, for use with [`archetypes::Transform3D`].
pub mod transform {
    pub use dl_sdk_types::datatypes::{Angle, Quaternion, RotationAxisAngle};
}

/// Coordinate system helpers, for use with [`components::ViewCoordinates`].
pub mod coordinates {
    pub use dl_sdk_types::view_coordinates::{Axis3, Handedness, Sign, SignedAxis3};
}

pub use dl_sdk_types::{archetypes, components, datatypes};

mod prelude {
    // Import all archetypes into the global namespace to minimize
    // the amount of typing for our users.
    // Also import any component or datatype that has a unique name:
    pub use dl_chunk::TimeColumn;
    pub use dl_sdk_types::archetypes::*;
    pub use dl_sdk_types::components::{
        AlbedoFactor, Color, FillMode, HalfSize2D, HalfSize3D, ImageFormat, LineStrip2D,
        LineStrip3D, MediaType, Position2D, Position3D, Radius, Scale3D, Text, TextLogLevel,
        TransformRelation, TriangleIndices, Vector2D, Vector3D,
    };
    pub use dl_sdk_types::datatypes::{
        Angle, AnnotationInfo, ChannelDatatype, ClassDescription, ColorModel, Float32,
        KeypointPair, Mat3x3, PixelFormat, Quaternion, Rgba32, RotationAxisAngle, TensorBuffer,
        TensorData, Vec2D, Vec3D, Vec4D,
    };
    // Special utility types.
    pub use dl_sdk_types::{AnyValues, DynamicArchetype, Rotation3D};
}
pub use prelude::*;
