#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    // Open a local file handle to stream the data into.
    const auto rec = dalaran::RecordingStream("dalaran_example_log_to_dlr");
    rec.save("/tmp/my_recording.dlr").exit_on_failure();

    // Log data as usual, thereby writing it into the file.
    while (true) {
        rec.log("log", dalaran::TextLog("Logging things…"));
    }
}
