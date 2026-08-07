"""Log arbitrary archetype data."""

import dalaran as dl

dl.init("dalaran_example_dynamic_archetype", spawn=True)

dl.log(
    "new_archetype",
    dl
    .DynamicArchetype(
        archetype="MyArchetype",
        components={
            # Using arbitrary Arrow data.
            "homepage": "https://www.dalaran.dev",
            "repository": "https://github.com/rerun-io/rerun",
        },
    )
    # Using Dalaran's builtin components.
    .with_component_override(
        "confidence", dl.components.ScalarBatch._COMPONENT_TYPE, [1.2, 3.4, 5.6]
    )
    .with_component_override(
        "description", dl.components.TextBatch._COMPONENT_TYPE, "Bla bla bla…"
    ),
)
