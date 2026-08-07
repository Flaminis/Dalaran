/// Demonstrates how to implement custom archetypes and components, and extend existing ones.

#include <dalaran.hpp>
#include <dalaran/demo_utils.hpp>

/// A custom component type.
struct Confidence {
    float value;
};

template <>
struct dalaran::Loggable<Confidence> {
    static constexpr std::string_view ComponentType = "user.Confidence";

    static const std::shared_ptr<arrow::DataType>& arrow_datatype() {
        return dalaran::Loggable<dalaran::Float32>::arrow_datatype();
    }

    // TODO(#4257) should take a dalaran::Collection instead of pointer and size.
    static dalaran::Result<std::shared_ptr<arrow::Array>> to_arrow(
        const Confidence* instances, size_t num_instances
    ) {
        return dalaran::Loggable<dalaran::Float32>::to_arrow(
            reinterpret_cast<const dalaran::Float32*>(instances),
            num_instances
        );
    }
};

/// A custom archetype that extends Dalaran's builtin `dalaran::Points3D` archetype with a custom component.
struct CustomPoints3D {
    dalaran::Points3D points;
    // Using a dalaran::Collection is not strictly necessary, you could also use an std::vector for example,
    // but useful for avoiding allocations since `dalaran::Collection` can borrow data from other containers.
    std::optional<dalaran::Collection<Confidence>> confidences;
};

template <>
struct dalaran::AsComponents<CustomPoints3D> {
    static Result<dalaran::Collection<ComponentBatch>> as_batches(
        const CustomPoints3D& archetype
    ) {
        auto batches =
            AsComponents<dalaran::Points3D>::as_batches(archetype.points)
                .value_or_throw()
                .to_vector();

        // Add custom confidence components if present.
        if (archetype.confidences) {
            auto descriptor =
                dalaran::ComponentDescriptor("user.CustomPoints3D:confidences")
                    .or_with_archetype("user.CustomPoints3D")
                    .or_with_component_type(
                        dalaran::Loggable<Confidence>::ComponentType
                    );
            batches.push_back(ComponentBatch::from_loggable(
                                  *archetype.confidences,
                                  descriptor
            )
                                  .value_or_throw());
        }

        return dalaran::take_ownership(std::move(batches));
    }
};

// ---

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_custom_data");
    rec.spawn().exit_on_failure();

    auto grid = dalaran::demo::grid3d<dalaran::Position3D, float>(-5.0f, 5.0f, 3);

    rec.log(
        "left/my_confident_point_cloud",
        CustomPoints3D{
            dalaran::Points3D(grid),
            Confidence{42.0f},
        }
    );

    std::vector<Confidence> confidences;
    for (auto i = 0; i < 27; ++i) {
        confidences.emplace_back(Confidence{static_cast<float>(i)});
    }

    rec.log(
        "right/my_polarized_point_cloud",
        CustomPoints3D{
            dalaran::Points3D(grid),
            confidences,
        }
    );
}
