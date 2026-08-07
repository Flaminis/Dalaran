//! Demonstrates how to implement custom archetypes and components, and extend existing ones.

use dalaran::{
    ComponentBatch as _, ComponentDescriptor, SerializedComponentBatch,
    demo_util::grid,
    external::{arrow, glam, dl_sdk_types},
};

// ---

/// A custom [component bundle] that extends Dalaran's builtin [`dalaran::Points3D`] archetype with extra
/// [`dalaran::Component`]s.
///
/// [component bundle]: [`AsComponents`]
struct CustomPoints3D {
    points3d: dalaran::Points3D,
    confidences: Option<Vec<Confidence>>,
}

impl dalaran::AsComponents for CustomPoints3D {
    fn as_serialized_batches(&self) -> Vec<SerializedComponentBatch> {
        std::iter::chain(
            self.points3d.as_serialized_batches(),
            std::iter::once(self.confidences.as_ref().and_then(|batch| {
                batch.serialized(ComponentDescriptor {
                    archetype: Some("user.CustomPoints3D".into()),
                    component: "user.CustomPoints3D:confidences".into(),
                    component_type: Some(
                        <Confidence as dalaran::Component>::name(),
                    ),
                })
            }))
            .flatten(),
        )
        .collect()
    }
}

// ---

/// A custom [`dalaran::Component`] that is backed by a builtin [`dalaran::Float32`] scalar.
#[derive(Debug, Clone, Copy, dalaran::SizeBytes)]
struct Confidence(dalaran::Float32);

impl From<f32> for Confidence {
    fn from(v: f32) -> Self {
        Self(dalaran::Float32(v))
    }
}

impl dalaran::Loggable for Confidence {
    #[inline]
    fn arrow_datatype() -> arrow::datatypes::DataType {
        dalaran::Float32::arrow_datatype()
    }

    #[inline]
    fn to_arrow_opt<'a>(
        data: impl IntoIterator<
            Item = Option<impl Into<std::borrow::Cow<'a, Self>>>,
        >,
    ) -> dl_sdk_types::SerializationResult<arrow::array::ArrayRef>
    where
        Self: 'a,
    {
        dalaran::Float32::to_arrow_opt(
            data.into_iter().map(|opt| opt.map(Into::into).map(|c| c.0)),
        )
    }
}

impl dalaran::Component for Confidence {
    #[inline]
    fn name() -> dalaran::ComponentType {
        "user.Confidence".into()
    }
}

// ---

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_custom_data")
        .spawn()?;

    rec.log(
        "left/my_confident_point_cloud",
        &CustomPoints3D {
            points3d: dalaran::Points3D::new(grid(
                glam::Vec3::splat(-5.0),
                glam::Vec3::splat(5.0),
                3,
            )),
            confidences: Some(vec![42f32.into()]),
        },
    )?;

    rec.log(
        "right/my_polarized_point_cloud",
        &CustomPoints3D {
            points3d: dalaran::Points3D::new(grid(
                glam::Vec3::splat(-5.0),
                glam::Vec3::splat(5.0),
                3,
            )),
            confidences: Some(
                (0..27).map(|i| i as f32).map(Into::into).collect(),
            ),
        },
    )?;

    Ok(())
}
