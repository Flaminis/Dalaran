// Log a scalar over time.

#include <dalaran.hpp>

#include <cmath>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_scalar");
    rec.spawn().exit_on_failure();

    // Log the data on a timeline called "step".
    for (int step = 0; step < 64; ++step) {
        rec.set_time_sequence("step", step);
        rec.log(
            "scalar",
            dalaran::Scalars(std::sin(static_cast<double>(step) / 10.0))
        );
    }
}
