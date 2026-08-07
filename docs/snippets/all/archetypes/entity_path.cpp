// Log a `TextDocument`

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_entity_path");
    rec.spawn().exit_on_failure();

    rec.log(
        R"(world/42/escaped\ string\!)",
        dalaran::TextDocument("This entity path was escaped manually")
    );
    rec.log(
        dalaran::new_entity_path(
            {"world", std::to_string(42), "unescaped string!"}
        ),
        dalaran::TextDocument(
            "This entity path was provided as a list of unescaped strings"
        )
    );

    assert(dalaran::escape_entity_path_part("my string!") == R"(my\ string\!)");
    assert(
        dalaran::new_entity_path({"world", "42", "my string!"}) ==
        R"(/world/42/my\ string\!)"
    );
}
