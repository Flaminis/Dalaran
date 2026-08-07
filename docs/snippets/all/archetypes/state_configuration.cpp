// Log a `StateChange` together with a `StateConfiguration` that customizes its display.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_state_configuration");
    rec.spawn().exit_on_failure();

    // Configure how each raw state value is displayed (label, color, visibility).
    rec.log_static(
        "door",
        dalaran::StateConfiguration()
            .with_values({"open", "closed"})
            .with_labels({"Open", "Closed"})
            .with_colors({0x4CAF50FF, 0xEF5350FF})
    );

    rec.set_time_sequence("step", 0);
    rec.log("door", dalaran::StateChange().with_state({"open"}));

    rec.set_time_sequence("step", 1);
    rec.log("door", dalaran::StateChange().with_state({"closed"}));

    rec.set_time_sequence("step", 2);
    rec.log("door", dalaran::StateChange().with_state({"open"}));
}
