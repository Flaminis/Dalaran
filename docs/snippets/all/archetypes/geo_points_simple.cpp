// Log some very simple geospatial point.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_geo_points");
    rec.spawn().exit_on_failure();

    rec.log(
        "dalaran_hq",
        dalaran::GeoPoints::from_lat_lon({{59.319221, 18.075631}})
            .with_radii(dalaran::Radius::ui_points(10.0f))
            .with_colors(dalaran::Color(255, 0, 0))
    );
}
