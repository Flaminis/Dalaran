// Log a `StateChange`

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_state_change");
    rec.spawn().exit_on_failure();

    rec.set_time_sequence("step", 0);
    rec.log("door", dalaran::StateChange().with_state({"open"}));

    rec.set_time_sequence("step", 1);
    rec.log("door", dalaran::StateChange().with_state({"closed"}));

    rec.set_time_sequence("step", 2);
    rec.log("door", dalaran::StateChange().with_state({"open"}));
}
