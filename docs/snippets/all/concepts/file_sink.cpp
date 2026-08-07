// Create and set a file sink.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_file_sink");

    rec.set_sinks(dalaran::FileSink{"recording.dlr"}).exit_on_failure();
}
