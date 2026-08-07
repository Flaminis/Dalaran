#include <dalaran.hpp>

struct CustomPosition3D {
    dalaran::Position3D position;
};

template <>
struct dalaran::Loggable<CustomPosition3D> {
    static constexpr const ComponentDescriptor Descriptor = ComponentDescriptor(
        "user.CustomArchetype", "user.CustomArchetype:custom_positions",
        "user.CustomPosition3D"
    );

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

int main(int argc, char* argv[]) {
    const auto rec =
        dalaran::RecordingStream("dalaran_example_descriptors_custom_component");
    rec.spawn().exit_on_failure();

    rec.log_static(
        "data",
        dalaran::ComponentBatch::from_loggable<dalaran::Position3D>(
            {1.0f, 2.0f, 3.0f},
            dalaran::Loggable<CustomPosition3D>::Descriptor
        )
    );

    // The tags are indirectly checked by the Rust version (have a look over there for more info).
}
