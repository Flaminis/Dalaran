//! Query and display the first 10 rows of a recording in a dataframe view.
//!
//! The blueprint is being loaded from an existing blueprint recording file.

// cargo r -p snippets -- dataframe_view_query_external /tmp/dna.dlr /tmp/dna.dbl

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = std::env::args().collect::<Vec<_>>();

    let path_to_dlr = &args[1];
    let path_to_dbl = &args[2];

    let rec = dalaran::RecordingStreamBuilder::new(
        "dalaran_example_dataframe_view_query_external",
    )
    .spawn()?;

    rec.log_file_from_path(
        path_to_dlr,
        None,  /* prefix */
        false, /* static */
    )?;
    rec.log_file_from_path(
        path_to_dbl,
        None,  /* prefix */
        false, /* static */
    )?;

    Ok(())
}
