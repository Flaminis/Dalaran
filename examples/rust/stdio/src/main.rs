//! Demonstrates how to log data to standard output with the Dalaran SDK, and then visualize it
//! from standard input with the Dalaran Viewer.
//!
//! Usage:
//! ```text
//! echo 'hello from stdin!' | cargo run | dalaran -
//! ```

use itertools::Itertools as _;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let rec = dalaran::RecordingStreamBuilder::new("dalaran_example_stdio").stdout()?;

    let lines: Vec<String> = std::io::stdin().lines().try_collect()?;
    let input = lines.join("\n");

    rec.log("stdin", &dalaran::TextDocument::new(input))?;

    Ok(())
}
