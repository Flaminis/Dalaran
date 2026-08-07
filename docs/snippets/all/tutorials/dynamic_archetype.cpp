// Log arbitrary archetype data.

#include <dalaran.hpp>

#include <arrow/array/builder_binary.h>
#include <arrow/array/builder_primitive.h>
#include <cstdio>

arrow::Status run_main() {
    const auto rec = dalaran::RecordingStream("dalaran_example_dynamic_archetype");
    rec.spawn().exit_on_failure();

    std::shared_ptr<arrow::Array> arrow_array;

    arrow::DoubleBuilder confidences_builder;
    ARROW_RETURN_NOT_OK(confidences_builder.AppendValues({1.2, 3.4, 5.6}));
    ARROW_RETURN_NOT_OK(confidences_builder.Finish(&arrow_array));
    auto confidences = dalaran::ComponentBatch::from_arrow_array(
        std::move(arrow_array),
        dalaran::ComponentDescriptor("MyArchetype:confidence")
            .with_component_type(dalaran::Loggable<dalaran::Scalar>::ComponentType)
            .with_archetype("MyArchetype")
    );

    arrow::StringBuilder description_builder;
    ARROW_RETURN_NOT_OK(description_builder.Append("Bla bla bla…"));
    ARROW_RETURN_NOT_OK(description_builder.Finish(&arrow_array));
    auto description = dalaran::ComponentBatch::from_arrow_array(
        std::move(arrow_array),
        dalaran::ComponentDescriptor("MyArchetype:description")
            .with_component_type(

                dalaran::Loggable<dalaran::Text>::ComponentType
            )
            .with_archetype("MyArchetype")
    );
    // URIs will become clickable links
    arrow::StringBuilder homepage_builder;
    ARROW_RETURN_NOT_OK(homepage_builder.Append("https://www.dalaran.dev"));
    ARROW_RETURN_NOT_OK(homepage_builder.Finish(&arrow_array));
    auto homepage = dalaran::ComponentBatch::from_arrow_array(
        std::move(arrow_array),
        dalaran::ComponentDescriptor("MyArchetype:homepage")
            .with_archetype("MyArchetype")
    );

    arrow::StringBuilder repository_builder;
    ARROW_RETURN_NOT_OK(
        repository_builder.Append("https://github.com/Flaminis/Dalaran")
    );
    ARROW_RETURN_NOT_OK(repository_builder.Finish(&arrow_array));
    auto repository = dalaran::ComponentBatch::from_arrow_array(
        std::move(arrow_array),
        dalaran::ComponentDescriptor("MyArchetype:repository")
            .with_archetype("MyArchetype")
    );

    rec.log("new_archetype", confidences, description, homepage, repository);

    return arrow::Status::OK();
}

int main(int argc, char* argv[]) {
    arrow::Status status = run_main();
    if (!status.ok()) {
        printf("%s\n", status.ToString().c_str());
        return 1;
    }
    return 0;
}
