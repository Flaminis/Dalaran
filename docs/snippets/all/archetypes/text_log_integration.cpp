/// Shows integration of Dalaran's `TextLog` with the C++ Loguru logging library
/// (https://github.com/emilk/loguru).

#include <loguru.hpp>
#include <dalaran.hpp>

void loguru_to_dalaran(void* user_data, const loguru::Message& message) {
    // NOTE: `dalaran::RecordingStream` is thread-safe.
    const dalaran::RecordingStream* rec =
        reinterpret_cast<const dalaran::RecordingStream*>(user_data);

    dalaran::TextLogLevel level;
    if (message.verbosity == loguru::Verbosity_FATAL) {
        level = dalaran::TextLogLevel::Critical;
    } else if (message.verbosity == loguru::Verbosity_ERROR) {
        level = dalaran::TextLogLevel::Error;
    } else if (message.verbosity == loguru::Verbosity_WARNING) {
        level = dalaran::TextLogLevel::Warning;
    } else if (message.verbosity == loguru::Verbosity_INFO) {
        level = dalaran::TextLogLevel::Info;
    } else if (message.verbosity == loguru::Verbosity_1) {
        level = dalaran::TextLogLevel::Debug;
    } else if (message.verbosity == loguru::Verbosity_2) {
        level = dalaran::TextLogLevel::Trace;
    } else {
        level = dalaran::TextLogLevel(std::to_string(message.verbosity));
    }

    rec->log(
        "logs/handler/text_log_integration",
        dalaran::TextLog(message.message).with_level(level)
    );
}

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_text_log_integration");
    rec.spawn().exit_on_failure();

    // Log a text entry directly:
    rec.log(
        "logs",
        dalaran::TextLog("this entry has loglevel TRACE")
            .with_level(dalaran::TextLogLevel::Trace)
    );

    loguru::add_callback(
        "dalaran",
        loguru_to_dalaran,
        const_cast<void*>(reinterpret_cast<const void*>(&rec)),
        loguru::Verbosity_INFO
    );

    LOG_F(
        INFO,
        "This INFO log got added through the standard logging interface"
    );

    // we need to do this before `rec` goes out of scope:
    loguru::remove_callback("dalaran");
}
