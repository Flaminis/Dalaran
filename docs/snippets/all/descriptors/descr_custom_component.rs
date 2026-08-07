use dalaran::{
    ChunkStore, ChunkStoreConfig, ComponentBatch as _, ComponentDescriptor,
};

fn example(
    rec: &dalaran::RecordingStream,
) -> Result<(), Box<dyn std::error::Error>> {
    let positions = dalaran::components::Position3D::new(1.0, 2.0, 3.0)
        .try_serialized(ComponentDescriptor {
            archetype: Some("user.CustomArchetype".into()),
            component: "user.CustomArchetype:custom_positions".into(),
            component_type: Some("user.CustomPosition3D".into()),
        })?;
    rec.log_serialized_batches("data", true, [positions])?;

    Ok(())
}

// ---
// Everything below this line is _not_ part of the example.
// This is internal testing code to make sure the example yields the right data.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    const APP_ID: &str = "dalaran_example_descriptors_custom_component";
    let rec = dalaran::RecordingStreamBuilder::new(APP_ID).spawn()?;

    example(&rec)?;

    check_tags(&rec);

    Ok(())
}

#[expect(clippy::unwrap_used)]
fn check_tags(rec: &dalaran::RecordingStream) {
    // When this snippet runs through the snippet comparison machinery, this environment variable
    // will point to the output DLR.
    // We can thus load this DLR to check that the proper tags were indeed forwarded.
    //
    // Python and C++ are indirectly checked by the snippet comparison tool itself.
    if let Ok(path_to_dlr) = std::env::var("_DALARAN_TEST_FORCE_SAVE") {
        rec.flush_blocking().unwrap();

        let mut dlr_file = std::fs::File::open(&path_to_dlr).unwrap();
        let stores = ChunkStore::from_dlr_reader(
            &ChunkStoreConfig::ALL_DISABLED,
            &mut dlr_file,
        )
        .unwrap();
        assert_eq!(1, stores.len());

        let store = stores.into_values().next().unwrap();
        // Skip the first chunk, as it represents the `RecordingInfo`.
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
                archetype: Some("user.CustomArchetype".into()),
                component: "user.CustomArchetype:custom_positions".into(),
                component_type: Some("user.CustomPosition3D".into()),
            }, //
        ];

        similar_asserts::assert_eq!(expected, descriptors);
    }
}
