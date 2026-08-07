//! Log a PNG image

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_encoded_image")
        .spawn()?;

    let image = include_bytes!("ferris.png");

    rec.log(
        "image",
        &dalaran::EncodedImage::from_file_contents(image.to_vec()),
    )?;

    Ok(())
}
