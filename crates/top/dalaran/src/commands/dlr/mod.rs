mod compare;
mod filter;
mod merge_optimize;
mod migrate;
mod print;
mod route;
mod split;
mod stats;
mod verify;

// ---
use anyhow::Context as _;
use clap::Subcommand;

use self::compare::CompareCommand;
use self::filter::FilterCommand;
use self::merge_optimize::{CompactCommand, MergeCommand, OptimizeCommand};
use self::migrate::MigrateCommand;
use self::print::PrintCommand;
use self::route::RouteCommand;
use self::split::SplitCommand;
use self::stats::StatsCommand;
use self::verify::VerifyCommand;

/// Manipulate the contents of .dlr and .dbl files.
#[derive(Debug, Clone, Subcommand)]
pub enum RrdCommands {
    /// Compares the data between 2 .dlr files, returning a successful shell exit code if they
    /// match.
    ///
    /// This ignores the `log_time` timeline.
    Compare(CompareCommand),

    /// Filters out data from .dlr/.dbl files/streams, and writes the result to standard output.
    ///
    /// Reads from standard input if no paths are specified.
    ///
    /// This will not affect the chunking of the data in any way.
    ///
    /// Example: `dalaran dlr filter --drop-timeline log_tick /my/recordings/*.dlr > output.dlr`
    Filter(FilterCommand),

    /// Merges the contents of multiple .dlr/.dbl files/streams, and writes the result to standard output.
    ///
    /// Reads from standard input if no paths are specified.
    ///
    /// ⚠️ This will automatically migrate the data to the latest version of the DLR protocol, if needed. ⚠️
    ///
    /// Example: `dalaran dlr merge /my/recordings/*.dlr > output.dlr`
    Merge(MergeCommand),

    /// Migrate one or more .dlr files to the newest Dalaran version.
    ///
    /// Example: `dalaran dlr migrate foo.dlr`
    /// Results in a `foo.backup.dlr` (copy of the old file) and a new `foo.dlr` (migrated).
    Migrate(MigrateCommand),

    /// Optimizes the contents of one or more .dlr/.dbl files/streams by compacting chunks, and writes the result to standard output.
    ///
    /// Reads from standard input if no paths are specified.
    ///
    /// If any input is a directory, the command switches to **directory mirror mode**:
    /// every `.dlr`/`.dbl` file under the input is optimized independently, and written
    /// to the output path while preserving the input folder structure. In this mode the
    /// output (`-o`) must be set and is treated as a directory root.
    ///
    /// Uses the usual environment variables to control the compaction thresholds:
    /// `DALARAN_CHUNK_MAX_ROWS`,
    /// `DALARAN_CHUNK_MAX_ROWS_IF_UNSORTED`,
    /// `DALARAN_CHUNK_MAX_BYTES`.
    ///
    /// Unless explicit flags are passed, in which case they will override environment values.
    ///
    /// Video stream chunks are also rebatched on GoP (keyframe) boundaries so that each
    /// chunk holds one or more complete GoPs. Pass `--no-rebatch-videos` to disable that.
    ///
    /// ⚠️ This will automatically migrate the data to the latest version of the DLR protocol, if needed. ⚠️
    ///
    /// Examples:
    ///
    /// * Optimize a single recording into one optimized file (`-o`):
    ///   `dalaran dlr optimize my.dlr -o my-compacted.dlr`
    ///
    /// * Merge many recordings into one optimized file:
    ///   `dalaran dlr optimize --max-size 2MiB /my/recordings/*.dlr -o output.dlr`
    ///
    /// * Pipe through stdin/stdout, overriding both row and size thresholds:
    ///   `cat my.dlr | dalaran dlr optimize --max-rows 4096 --max-size 2MiB > output.dlr`
    ///
    /// * Directory mirror mode — optimize every `.dlr`/`.dbl` under a tree, preserving structure:
    ///   `dalaran dlr optimize --max-size 2MiB /my/recordings -o /my/recordings-compacted`
    Optimize(OptimizeCommand),

    /// Deprecated: renamed to `optimize`.
    #[command(hide = true)]
    Compact(CompactCommand),

    /// Print the contents of one or more .dlr/.dbl files/streams.
    ///
    /// Reads from standard input if no paths are specified.
    ///
    /// Example: `dalaran dlr print /my/recordings/*.dlr`
    Print(PrintCommand),

    /// Manipulates the metadata of log message streams without decoding the payloads.
    ///
    /// This can be used to combine multiple .dlr files into a single recording.
    /// Example: `dalaran dlr route --recording-id my_recording /my/recordings/*.dlr > output.dlr`
    ///
    /// Note: Because the payload of the messages is never decoded, no migration or verification will performed.
    Route(RouteCommand),

    /// Optimally splits a recording on a specified timeline.
    ///
    /// The sum of the generated splits will always exactly match the original recording.
    ///
    /// Example: `dalaran dlr split --output-dir ./splits --timeline log_tick --time 33 --time 66 ./my_video.dlr`
    Split(SplitCommand),

    /// Compute important statistics for one or more .dlr/.dbl files/streams.
    ///
    /// Reads from standard input if no paths are specified.
    ///
    /// Example: `dalaran dlr stats /my/recordings/*.dlr`
    Stats(StatsCommand),

    /// Verify the that the .dlr file can be loaded and correctly interpreted.
    ///
    /// Can be used to ensure that the current Dalaran version can load the data.
    Verify(VerifyCommand),
}

impl RrdCommands {
    pub fn run(self) -> anyhow::Result<()> {
        match self {
            Self::Compare(cmd) => {
                cmd.run()
                    // Print current directory, this can be useful for debugging issues with relative paths.
                    .with_context(|| format!("current directory {:?}", std::env::current_dir()))
            }
            Self::Optimize(cmd) => cmd.run(),
            Self::Compact(cmd) => cmd.run(),
            Self::Filter(cmd) => cmd.run(),
            Self::Split(cmd) => cmd.run(),
            Self::Merge(cmd) => cmd.run(),
            Self::Migrate(cmd) => cmd.run(),
            Self::Print(cmd) => cmd.run(),
            Self::Route(cmd) => cmd.run(),
            Self::Stats(cmd) => cmd.run(),
            Self::Verify(cmd) => cmd.run(),
        }
    }
}
