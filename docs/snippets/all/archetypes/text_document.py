"""Log a `TextDocument`."""

import dalaran as dl

dl.init("dalaran_example_text_document", spawn=True)

dl.log("text_document", dl.TextDocument("Hello, TextDocument!"))

dl.log(
    "markdown",
    dl.TextDocument(
        '''
# Hello Markdown!
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

Of course you can also have [normal https links](https://github.com/rerun-io/rerun), e.g. <https://dalaran.dev>.

## Image
![A random image](https://picsum.photos/640/480)
'''.strip(),
        media_type=dl.MediaType.MARKDOWN,
    ),
)
