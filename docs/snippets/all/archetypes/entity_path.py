import dalaran as dl

dl.init("dalaran_example_entity_path", spawn=True)

dl.log(
    r"world/42/escaped\ string\!",
    dl.TextDocument("This entity path was escaped manually"),
)
dl.log(
    ["world", 42, "unescaped string!"],
    dl.TextDocument(
        "This entity path was provided as a list of unescaped strings"
    ),
)

assert dl.escape_entity_path_part("my string!") == r"my\ string\!"
assert (
    dl.new_entity_path(["world", 42, "my string!"]) == r"/world/42/my\ string\!"
)
