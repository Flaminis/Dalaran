use dalaran::external::ndarray;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_image_formats")
        .spawn()?;

    // Simple gradient image
    let image =
        ndarray::Array3::from_shape_fn((256, 256, 3), |(y, x, c)| match c {
            0 => x as u8,
            1 => (x + y).min(255) as u8,
            2 => y as u8,
            _ => unreachable!(),
        });

    // RGB image
    rec.log(
        "image_rgb",
        &dalaran::Image::from_color_model_and_tensor(
            dalaran::ColorModel::RGB,
            image.clone(),
        )?,
    )?;

    // Green channel only (Luminance)
    rec.log(
        "image_green_only",
        &dalaran::Image::from_color_model_and_tensor(
            dalaran::ColorModel::L,
            image.slice(ndarray::s![.., .., 1]).to_owned(),
        )?,
    )?;

    // BGR image
    rec.log(
        "image_bgr",
        &dalaran::Image::from_color_model_and_tensor(
            dalaran::ColorModel::BGR,
            image.slice(ndarray::s![.., .., ..;-1]).to_owned(),
        )?,
    )?;

    // New image with Separate Y/U/V planes with 4:2:2 chroma downsampling
    let mut yuv_bytes = Vec::with_capacity(256 * 256 + 128 * 256 * 2);
    yuv_bytes.extend(std::iter::repeat_n(128, 256 * 256)); // Fixed value for Y.
    yuv_bytes.extend((0..256).flat_map(|_y| (0..128).map(|x| x * 2))); // Gradient for U.
    yuv_bytes.extend((0..256).flat_map(|y| std::iter::repeat_n(y as u8, 128))); // Gradient for V.
    rec.log(
        "image_yuv422",
        &dalaran::Image::from_pixel_format(
            [256, 256],
            dalaran::PixelFormat::Y_U_V16_FullRange,
            yuv_bytes,
        ),
    )?;

    Ok(())
}
