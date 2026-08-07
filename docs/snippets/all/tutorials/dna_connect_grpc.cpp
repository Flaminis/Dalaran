// The DNA-abacus example, connecting to a separately-running viewer over gRPC.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    // Connect to the viewer running at the default URL.
    const auto rec = dalaran::RecordingStream("dalaran_example_dna_abacus");
    rec.connect_grpc().exit_on_failure();

    // … log data as in the spawn-based example …
}
