// Create and set a GRPC sink.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_grpc_sink");

    // The default URL is `dalaran+http://127.0.0.1:9876/proxy`
    // This can be used to connect to a viewer on a different machine
    rec.set_sinks(dalaran::GrpcSink{"dalaran+http://127.0.0.1:9876/proxy"})
        .exit_on_failure();
}
