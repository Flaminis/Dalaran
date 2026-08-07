use dalaran::{
    ChunkStore, ChunkStoreConfig, ComponentBatch as _, ComponentDescriptor,
};

struct CustomPoints3D {
    positions: Vec<dalaran::components::Position3D>,
    colors: Option<Vec<dalaran::components::Color>>,
}

impl CustomPoints3D {
    fn overridden_position_descriptor() -> ComponentDescriptor {
        ComponentDescriptor {
            archetype: Some("user.CustomPoints3D".into()),
            component: "user.CustomPoints3D:custom_positions".into(),
            component_type: Some("user.CustomPosition3D".into()),
        }
    }

    fn overridden_color_descriptor() -> ComponentDescriptor {
        ComponentDescriptor::partial("user.CustomPoints3D:colors")
            .or_with_archetype(|| "user.CustomPoints3D".into())
            .or_with_component_type(
                <dalaran::components::Color as dalaran::Component>::name,
            )
    }
}

impl dalaran::AsComponents for CustomPoints3D {
    fn as_serialized_batches(&self) -> Vec<dalaran::SerializedComponentBatch> {
        [
            self.positions
                .serialized(Self::overridden_position_descriptor()),
            self.colors.as_ref().and_then(|colors| {
                colors.serialized(Self::overridden_color_descriptor())
            }),
        ]
        .into_iter()
        .flatten()
        .collect()
    }
}

fn example(
    rec: &dalaran::RecordingStream,
) -> Result<(), Box<dyn std::error::Error>> {
    let positions = dalaran::components::Position3D::new(1.0, 2.0, 3.0);
    let colors = dalaran::components::Color::new(0xFF00FFFF);

    let points = CustomPoints3D {
        positions: vec![positions],
        colors: Some(vec![colors]),
    };

    rec.log_static("data", &points)?;

    Ok(())
}

// ---
// Everything below this line is _not_ part of the example.
// This is internal testing code to make sure the example yields the right data.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    const APP_ID: &str = "dalaran_example_descriptors_custom_archetype";
    let rec = dalaran::RecordingStreamBuilder::new(APP_ID).spawn()?;

    example(&rec)?;

    check_tags(&rec);

    Ok(())
}

#[expect(clippy::unwrap_used)]
fn check_tags(rec: &dalaran::RecordingStream) {
    // When this snippet runs through the snippet comparison machinery, this environment variable
    // will point to the output RRD.
    // We can thus load this RRD to check that the proper tags were indeed forwarded.
    //
    // Python and C++ are indirectly checked by the snippet comparison tool itself.
    if let Ok(path_to_rrd) = std::env::var("_DALARAN_TEST_FORCE_SAVE") {
        rec.flush_blocking().unwrap();

        let mut rrd_file = std::fs::File::open(&path_to_rrd).unwrap();
        let stores = ChunkStore::from_rrd_reader(
            &ChunkStoreConfig::ALL_DISABLED,
            &mut rrd_file,
        )
        .unwrap();
        assert_eq!(1, stores.len());

        let store = stores.into_values().next().unwrap();
        // Skip the first chunk, as it represent the `RecordingInfo`.
        let chunks = store.iter_physical_chunks().skip(1).collect::<Vec<_>>();
        assert_eq!(1, chunks.len());

        let chunk = chunks.into_iter().next().unwrap();

        let mut descriptors = chunk
            .components()
            .component_descriptors()
            .cloned()
            .collect::<Vec<_>>();
        descriptors.sort();

        let expected = vec![
            ComponentDescriptor {
                archetype: Some("user.CustomPoints3D".into()),
                component: "user.CustomPoints3D:colors".into(),
                component_type: Some("dalaran.components.Color".into()),
            },
            ComponentDescriptor {
                archetype: Some("user.CustomPoints3D".into()),
                component: "user.CustomPoints3D:custom_positions".into(),
                component_type: Some("user.CustomPosition3D".into()),
            },
        ];

        similar_asserts::assert_eq!(expected, descriptors);
    }
}
