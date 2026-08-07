#include <dalaran.hpp>
#include <vector>

struct CustomPosition3D {
    dalaran::Position3D position;
};

template <>
struct dalaran::Loggable<CustomPosition3D> {
    static constexpr ComponentDescriptor Descriptor = "user.CustomPosition3D";

    static const std::shared_ptr<arrow::DataType>& arrow_datatype() {
        return dalaran::Loggable<dalaran::Position3D>::arrow_datatype();
    }

    // TODO(#4257) should take a dalaran::Collection instead of pointer and size.
    static dalaran::Result<std::shared_ptr<arrow::Array>> to_arrow(
        const CustomPosition3D* instances, size_t num_instances
    ) {
        return dalaran::Loggable<dalaran::Position3D>::to_arrow(
            reinterpret_cast<const dalaran::Position3D*>(instances),
            num_instances
        );
    }
};

/// A custom archetype that extends Dalaran's builtin `dalaran::Points3D` archetype with a custom component.
struct CustomPoints3D {
    dalaran::Collection<CustomPosition3D> positions;
    std::optional<dalaran::Collection<dalaran::Color>> colors;
};

template <>
struct dalaran::AsComponents<CustomPoints3D> {
    static Result<dalaran::Collection<ComponentBatch>> as_batches(
        const CustomPoints3D& archetype
    ) {
        std::vector<dalaran::ComponentBatch> batches;

        auto positions_descr = dalaran::ComponentDescriptor(
            "user.CustomPoints3D",
            "user.CustomPoints3D:custom_positions",
            "user.CustomPosition3D"
        );
        batches.push_back(
            ComponentBatch::from_loggable(archetype.positions, positions_descr)
                .value_or_throw()
        );

        if (archetype.colors) {
            auto colors_descr =
                dalaran::ComponentDescriptor("user.CustomPoints3D:colors")
                    .with_archetype("user.CustomPoints3D")
                    .with_component_type(
                        dalaran::Loggable<dalaran::Color>::ComponentType
                    );
            batches.push_back(
                ComponentBatch::from_loggable(archetype.colors, colors_descr)
                    .value_or_throw()
            );
        }

        return dalaran::take_ownership(std::move(batches));
    }
};

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_descriptors_custom_archetype");
    rec.spawn().exit_on_failure();

    rec.log_static(
        "data",
        CustomPoints3D{
            CustomPosition3D{{1.0f, 2.0f, 3.0f}},
            dalaran::Color(0xFF00FFFF)
        }
    );

    // The tags are indirectly checked by the Rust version (have a look over there for more info).
}
