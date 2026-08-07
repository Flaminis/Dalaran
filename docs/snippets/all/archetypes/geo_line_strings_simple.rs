//! Log a simple geospatial line string.

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec =
        dalaran::RecordingStreamBuilder::new("dalaran_example_geo_line_strings")
            .spawn()?;

    rec.log(
        "colorado",
        &dalaran::GeoLineStrings::from_lat_lon([[
            [41.0000, -109.0452],
            [41.0000, -102.0415],
            [36.9931, -102.0415],
            [36.9931, -109.0452],
            [41.0000, -109.0452],
        ]])
        .with_radii([dalaran::Radius::new_ui_points(2.0)])
        .with_colors([dalaran::Color::from_rgb(0, 0, 255)]),
    )?;

    Ok(())
}
