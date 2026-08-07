#include <dalaran.hpp>

#include <cmath>

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_getting_started", "run-1");
    rec.save("run-1.rrd").exit_on_failure();

    for (int t = 0; t < 10; ++t) {
        rec.set_time_sequence("step", t);
        const auto tf = static_cast<double>(t);
        rec.log("/arm/shoulder", dalaran::Scalars(std::sin(tf * 0.5)));
        rec.log("/arm/elbow", dalaran::Scalars(std::cos(tf * 0.5)));
    }
}
