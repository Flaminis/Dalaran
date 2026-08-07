// Log a `TextLog`

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_text_log");
    rec.spawn().exit_on_failure();

    rec.log(
        "log",
        dalaran::TextLog("Application started.")
            .with_level(dalaran::TextLogLevel::Info)
    );
}
