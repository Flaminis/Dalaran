#include <iostream>
#include <sstream>

#if defined(WIN32)
#include <process.h>
#define getpid _getpid
#else
#include <unistd.h>
#endif

#include <dalaran.hpp>
#include <dalaran/demo_utils.hpp>

using dalaran::demo::grid3d;

int main() {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_shared_recording", "my_shared_recording");
    rec.spawn().exit_on_failure();

    rec.log("updates", dalaran::TextLog(std::string("Hello from ") + std::to_string(getpid())));

    std::cout << "Run me again to append more data to the recording!" << std::endl;
}
