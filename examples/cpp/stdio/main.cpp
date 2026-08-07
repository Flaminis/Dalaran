#include <iostream>
#include <string>

#include <dalaran.hpp>

int main() {
    const auto rec = dalaran::RecordingStream("dalaran_example_stdio");
    rec.to_stdout().exit_on_failure();

    std::string input;
    std::string line;
    while (std::getline(std::cin, line)) {
        input += line + '\n';
    }

    rec.log("stdin", dalaran::TextDocument(input));
}
