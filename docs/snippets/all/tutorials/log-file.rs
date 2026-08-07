    let args = std::env::args().collect::<Vec<_>>();

    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_log_file").spawn()?;

    rec.log_file_from_path(&args[1], None /* prefix */, true /* static */)?;
