// 0.8
use dalaran::{components::Point3D, MsgSender};
let positions = vec![Point3D::from([1.0, 2.0, 3.0])];

MsgSender::new("points")
    .with_component(&positions)?
    .send(&rec)?;

// 0.9
rec.log(
    "points",
    &dalaran::Points3D::new([(1.0, 2.0, 3.0)]),
)?;
