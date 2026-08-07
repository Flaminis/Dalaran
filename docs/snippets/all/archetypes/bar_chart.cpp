// Create and log a bar chart.

#include <dalaran.hpp>
#include <vector>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_bar_chart");
    rec.spawn().exit_on_failure();

    rec.log("bar_chart", dalaran::BarChart::i64({8, 4, 0, 9, 1, 4, 1, 6, 9, 0}));

    auto abscissa = std::vector<int64_t>{0, 1, 3, 4, 7, 11};
    auto abscissa_data =
        dalaran::TensorData(dalaran::Collection{abscissa.size()}, abscissa);
    rec.log(
        "bar_chart_custom_abscissa",
        dalaran::BarChart::i64({8, 4, 0, 9, 1, 4}).with_abscissa(abscissa_data)
    );

    auto widths = std::vector<float>{1, 2, 1, 3, 4, 1};
    rec.log(
        "bar_chart_custom_abscissa_and_widths",
        dalaran::BarChart::i64({8, 4, 0, 9, 1, 4})
            .with_abscissa(abscissa_data)
            .with_widths(widths)
    );
}
