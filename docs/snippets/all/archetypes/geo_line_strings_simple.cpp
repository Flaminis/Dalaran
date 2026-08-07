// Log a simple geospatial line string.

#include <dalaran.hpp>

int main(int argc, char* argv[]) {
    const auto rec = dalaran::RecordingStream("dalaran_example_geo_line_strings");
    rec.spawn().exit_on_failure();

    auto line_string = dalaran::GeoLineString::from_lat_lon(
        {{41.0000, -109.0452},
         {41.0000, -102.0415},
         {36.9931, -102.0415},
         {36.9931, -109.0452},
         {41.0000, -109.0452}}
    );

    rec.log(
        "colorado",
        dalaran::GeoLineStrings(line_string)
            .with_radii(dalaran::Radius::ui_points(2.0f))
            .with_colors(dalaran::Color(0, 0, 255))
    );
}
