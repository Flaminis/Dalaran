//! Log a pinhole and a random image.

use ndarray::{Array, ShapeBuilder as _};
use rand::prelude::*;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_pinhole").spawn()?;

    let mut image = Array::<u8, _>::default((3, 3, 3).f());
    let mut rng = rand::rngs::SmallRng::seed_from_u64(42);
    image.map_inplace(|x| *x = rng.random());

    rec.log(
        "world/image",
        &dalaran::Pinhole::from_focal_length_and_resolution([3., 3.], [3., 3.]),
    )?;
    rec.log(
        "world/image",
        &dalaran::Image::from_color_model_and_tensor(
            dalaran::ColorModel::RGB,
            image,
        )?,
    )?;

    Ok(())
}
