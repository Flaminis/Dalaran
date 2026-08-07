//! Case conversions, the way Dalaran likes them.

/// Converts a snake or pascal case input into a snake case output.
///
/// If the input contains multiple parts separated by dots, only the last part is converted.
pub fn to_snake_case(s: &str) -> String {
    use convert_case::{Boundary, Converter, Pattern};

    let dalaran_snake = Converter::new()
        .set_boundaries(&[
            Boundary::Hyphen,
            Boundary::Space,
            Boundary::Underscore,
            Boundary::Acronym,
            Boundary::LowerUpper,
        ])
        .set_pattern(Pattern::Lowercase)
        .set_delimiter("_");

    let mut parts: Vec<_> = s.split('.').map(ToOwned::to_owned).collect();
    if let Some(last) = parts.last_mut() {
        *last = last
            .replace("UVec", "uvec")
            .replace("IVec", "ivec")
            .replace("DVec", "dvec")
            .replace("UInt", "uint");
        *last = dalaran_snake.convert(last.as_str());
    }
    parts.join(".")
}

#[test]
fn test_to_snake_case() {
    assert_eq!(
        to_snake_case("dalaran.components.Position2D"),
        "dalaran.components.position2d"
    );
    assert_eq!(
        to_snake_case("dalaran.components.position2d"),
        "dalaran.components.position2d"
    );

    assert_eq!(
        to_snake_case("dalaran.datatypes.Utf8"),
        "dalaran.datatypes.utf8"
    );
    assert_eq!(
        to_snake_case("dalaran.datatypes.utf8"),
        "dalaran.datatypes.utf8"
    );

    assert_eq!(
        to_snake_case("dalaran.datatypes.UVec2D"),
        "dalaran.datatypes.uvec2d"
    );
    assert_eq!(
        to_snake_case("dalaran.datatypes.uvec2d"),
        "dalaran.datatypes.uvec2d"
    );
    assert_eq!(
        to_snake_case("dalaran.datatypes.IVec3D"),
        "dalaran.datatypes.ivec3d"
    );
    assert_eq!(
        to_snake_case("dalaran.datatypes.ivec3d"),
        "dalaran.datatypes.ivec3d"
    );

    assert_eq!(
        to_snake_case("dalaran.datatypes.UInt32"),
        "dalaran.datatypes.uint32"
    );
    assert_eq!(
        to_snake_case("dalaran.datatypes.uint32"),
        "dalaran.datatypes.uint32"
    );

    assert_eq!(
        to_snake_case("dalaran.archetypes.Points2DIndicator"),
        "dalaran.archetypes.points2d_indicator"
    );
    assert_eq!(
        to_snake_case("dalaran.archetypes.points2d_indicator"),
        "dalaran.archetypes.points2d_indicator"
    );

    assert_eq!(
        to_snake_case("dalaran.components.TranslationAndMat3x3"),
        "dalaran.components.translation_and_mat3x3"
    );
    assert_eq!(
        to_snake_case("dalaran.components.translation_and_mat3x3"),
        "dalaran.components.translation_and_mat3x3"
    );

    assert_eq!(
        to_snake_case("dalaran.components.AnnotationContext"),
        "dalaran.components.annotation_context"
    );
}

/// Converts a snake or pascal case input into a pascal case output.
///
/// If the input contains multiple parts separated by dots, only the last part is converted.
pub fn to_pascal_case(s: &str) -> String {
    use convert_case::{Boundary, Converter, Pattern};

    let dalaran_pascal = Converter::new()
        .set_boundaries(&[
            Boundary::Hyphen,
            Boundary::Space,
            Boundary::Underscore,
            Boundary::DigitUpper,
            Boundary::Acronym,
            Boundary::LowerUpper,
        ])
        .set_pattern(Pattern::Capital);

    let mut parts: Vec<_> = s.split('.').map(ToOwned::to_owned).collect();
    if let Some(last) = parts.last_mut() {
        *last = last
            .replace("uvec", "UVec")
            .replace("ivec", "IVec")
            .replace("dvec", "DVec")
            .replace("uint", "UInt")
            .replace("2d", "2D") // NOLINT
            .replace("3d", "3D") // NOLINT
            .replace("4d", "4D");
        *last = dalaran_pascal.convert(last.as_str());
    }
    parts.join(".")
}

#[test]
fn test_to_pascal_case() {
    assert_eq!(
        to_pascal_case("dalaran.components.position2d"),
        "dalaran.components.Position2D"
    );
    assert_eq!(
        to_pascal_case("dalaran.components.Position2D"),
        "dalaran.components.Position2D"
    );

    assert_eq!(
        to_pascal_case("dalaran.datatypes.uvec2d"),
        "dalaran.datatypes.UVec2D"
    );
    assert_eq!(
        to_pascal_case("dalaran.datatypes.UVec2D"),
        "dalaran.datatypes.UVec2D"
    );
    assert_eq!(
        to_pascal_case("dalaran.datatypes.ivec3d"),
        "dalaran.datatypes.IVec3D"
    );
    assert_eq!(
        to_pascal_case("dalaran.datatypes.IVec3D"),
        "dalaran.datatypes.IVec3D"
    );

    assert_eq!(
        to_pascal_case("dalaran.datatypes.uint32"),
        "dalaran.datatypes.UInt32"
    );
    assert_eq!(
        to_pascal_case("dalaran.datatypes.UInt32"),
        "dalaran.datatypes.UInt32"
    );

    assert_eq!(
        to_pascal_case("dalaran.archetypes.points2d_indicator"),
        "dalaran.archetypes.Points2DIndicator"
    );
    assert_eq!(
        to_pascal_case("dalaran.archetypes.Points2DIndicator"),
        "dalaran.archetypes.Points2DIndicator"
    );

    assert_eq!(
        to_pascal_case("dalaran.components.translation_and_mat3x3"),
        "dalaran.components.TranslationAndMat3x3"
    );
    assert_eq!(
        to_pascal_case("dalaran.components.TranslationAndMat3x3"),
        "dalaran.components.TranslationAndMat3x3"
    );
}

/// Converts a snake or pascal case input into "human case" output, i.e. start with upper case and continue with lower case.
///
/// If the input contains multiple parts separated by dots, only the last part is converted.
pub fn to_human_case(s: &str) -> String {
    use convert_case::{Boundary, Converter, Pattern};

    let dalaran_human = Converter::new()
        .set_boundaries(&[
            Boundary::Hyphen,
            Boundary::Space,
            Boundary::Underscore,
            Boundary::LowerDigit,
            Boundary::Acronym,
            Boundary::LowerUpper,
        ])
        .set_pattern(Pattern::Sentence)
        .set_delimiter(" ");

    let mut parts: Vec<_> = s.split('.').map(ToOwned::to_owned).collect();
    if let Some(last) = parts.last_mut() {
        *last = dalaran_human.convert(last.as_str());
        *last = last
            .replace("Uvec", "UVec")
            .replace("Ivec", "IVec")
            .replace("Uint", "UInt")
            .replace("U vec", "UVec")
            .replace("I vec", "IVec")
            .replace("U int", "UInt")
            .replace("Int 32", "Int32")
            .replace("mat 3x 3", "mat3x3")
            .replace("mat 4x 4", "mat4x4")
            .replace("2d", "2D") // NOLINT
            .replace("3d", "3D") // NOLINT
            .replace("4d", "4D");
    }
    parts.join(".")
}

#[test]
fn test_to_human_case() {
    assert_eq!(
        to_human_case("dalaran.components.position2d"),
        "dalaran.components.Position 2D"
    );
    assert_eq!(
        to_human_case("dalaran.components.Position2D"),
        "dalaran.components.Position 2D"
    );

    assert_eq!(
        to_human_case("dalaran.datatypes.uvec2d"),
        "dalaran.datatypes.UVec 2D"
    );
    assert_eq!(
        to_human_case("dalaran.datatypes.UVec2D"),
        "dalaran.datatypes.UVec 2D"
    );
    assert_eq!(
        to_human_case("dalaran.datatypes.ivec3d"),
        "dalaran.datatypes.IVec 3D"
    );
    assert_eq!(
        to_human_case("dalaran.datatypes.IVec3D"),
        "dalaran.datatypes.IVec 3D"
    );

    assert_eq!(
        to_human_case("dalaran.datatypes.uint32"),
        "dalaran.datatypes.UInt32"
    );
    assert_eq!(
        to_human_case("dalaran.datatypes.UInt32"),
        "dalaran.datatypes.UInt32"
    );

    assert_eq!(
        to_human_case("dalaran.archetypes.points2d_indicator"),
        "dalaran.archetypes.Points 2D indicator"
    );
    assert_eq!(
        to_human_case("dalaran.archetypes.Points2DIndicator"),
        "dalaran.archetypes.Points 2D indicator"
    );

    assert_eq!(
        to_human_case("dalaran.components.translation_and_mat3x3"),
        "dalaran.components.Translation and mat3x3"
    );
    assert_eq!(
        to_human_case("dalaran.components.TranslationAndMat3x3"),
        "dalaran.components.Translation and mat3x3"
    );
}
