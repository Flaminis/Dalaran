#![expect(clippy::cast_possible_wrap)]

use crate::points3d_shared::{Point3DInput, prepare_points3d};

const NUM_POINTS: usize = 1_000_000;

fn execute(rec: &dalaran::RecordingStream, input: Point3DInput) -> anyhow::Result<()> {
    dl_tracing::profile_function!();

    let Point3DInput {
        positions,
        colors,
        radii,
        label: _,
    } = input;

    for i in 0..NUM_POINTS {
        rec.set_time_sequence("my_timeline", i as i64);
        rec.log(
            "single_point",
            &dalaran::Points3D::new([positions[i]])
                .with_colors([colors[i]])
                .with_radii([radii[i]]),
        )?;
    }
    Ok(())
}

/// Log many individual points (position, color, radius), each with a different timestamp.
pub fn run(rec: &dalaran::RecordingStream) -> anyhow::Result<()> {
    dl_tracing::profile_function!();
    let input = std::hint::black_box(prepare_points3d(1337, NUM_POINTS));
    execute(rec, input)
}
