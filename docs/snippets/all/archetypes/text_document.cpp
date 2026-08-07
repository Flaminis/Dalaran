// Log a `TextDocument`

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_text_document");
    rec.spawn().exit_on_failure();

    rec.log("text_document", dalaran::TextDocument("Hello, TextDocument!"));

    rec.log(
        "markdown",
        dalaran::TextDocument(R"#(# Hello Markdown!
[Click here to see the raw text](recording://markdown:Text).

Basic formatting:

| **Feature**       | **Alternative** |
| ----------------- | --------------- |
| Plain             |                 |
| *italics*         | _italics_       |
| **bold**          | __bold__        |
| ~~strikethrough~~ |                 |
| `inline code`     |                 |

----------------------------------

## Support
- [x] [Commonmark](https://commonmark.org/help/) support
- [x] GitHub-style strikethrough, tables, and checkboxes
- Basic syntax highlighting for:
  - [x] C and C++
  - [x] Python
  - [x] Rust
  - [ ] Other languages

## Links
You can link to [an entity](recording://markdown),
a [specific instance of an entity](recording://markdown[#0]),
or a [specific component](recording://markdown:Text).

Of course you can also have [normal https links](https://github.com/Flaminis/Dalaran), e.g. <https://dalaran.dev>.

## Image
![A random image](https://picsum.photos/640/480))#")
            .with_media_type(dalaran::MediaType::markdown())
    );
}
